"""
Daraz Open Platform API Integration
Syncs orders from Daraz (Bangladesh e-commerce platform)
"""
import requests
import hashlib
import hmac
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from kafka_producer import KafkaProducerClient
from dlq_handler import send_to_market_dlq
from models import MarketOrder, validate_market_order
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class DarazIntegration:
    """
    Daraz Open Platform API client for order synchronization
    Documentation: https://open.daraz.com/doc/
    """
    
    def __init__(self):
        """Initialize Daraz API client"""
        self.app_key = Config.DARAZ_APP_KEY
        self.app_secret = Config.DARAZ_APP_SECRET
        self.api_url = Config.DARAZ_API_URL
        
        if not self.app_key or not self.app_secret:
            raise ValueError("DARAZ_APP_KEY and DARAZ_APP_SECRET must be configured")
        
        self.producer = KafkaProducerClient("source.market.daraz")
        self.scraped_count = 0
        self.failed_count = 0
        
        logger.info(f"✅ Daraz API client initialized")
    
    def _generate_signature(self, api_name: str, params: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for Daraz API
        
        Args:
            api_name: API endpoint name (e.g., '/orders/get')
            params: Request parameters
            
        Returns:
            HMAC signature string
        """
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Build canonical string
        canonical_string = api_name + ''.join([f"{k}{v}" for k, v in sorted_params])
        
        # Generate HMAC
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature
    
    def _make_request(
        self, 
        api_name: str, 
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to Daraz API
        
        Args:
            api_name: API endpoint (e.g., '/orders/get')
            params: Request parameters
            
        Returns:
            JSON response or None if failed
        """
        # Add required parameters
        params.update({
            'app_key': self.app_key,
            'timestamp': str(int(time.time() * 1000)),  # Milliseconds
            'sign_method': 'sha256'
        })
        
        # Generate signature
        params['sign'] = self._generate_signature(api_name, params)
        
        # Build URL
        url = f"{self.api_url}{api_name}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check API response code
            if data.get('code') != '0':
                logger.error(f"❌ Daraz API error: {data.get('message')}")
                return None
            
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None
    
    def sync_orders(
        self, 
        limit: int = 100,
        status: str = "pending",
        created_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Sync orders from Daraz
        
        Args:
            limit: Maximum orders to fetch
            status: Order status filter ('pending', 'ready_to_ship', 'delivered', etc.)
            created_after: Only fetch orders after this datetime
            
        Returns:
            List of order dictionaries
        """
        orders_data = []
        
        logger.info(f"🔍 Syncing Daraz orders (limit: {limit}, status: {status})")
        
        try:
            # Build parameters
            params = {
                'limit': min(limit, 100),  # Daraz max is 100
                'offset': 0,
                'status': status
            }
            
            if created_after:
                params['created_after'] = created_after.isoformat()
            else:
                # Default: last 24 hours
                params['created_after'] = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Fetch orders
            response = self._make_request('/orders/get', params)
            
            if not response or 'data' not in response:
                logger.warning("⚠️  No orders returned from Daraz API")
                return orders_data
            
            orders = response['data'].get('orders', [])
            logger.info(f"📊 Found {len(orders)} orders from Daraz")
            
            # Transform orders
            for order in orders:
                try:
                    # Get order details
                    order_detail = self._get_order_detail(order['order_id'])
                    
                    if order_detail:
                        # Process each item in the order
                        for item in order_detail.get('items', []):
                            order_data = self._transform_order(order_detail, item)
                            if order_data:
                                orders_data.append(order_data)
                                self.scraped_count += 1
                    
                    # Rate limiting (max 100 requests/minute)
                    time.sleep(0.6)  # 600ms between requests
                    
                except Exception as e:
                    logger.error(f"❌ Error processing order {order.get('order_id')}: {e}")
                    self.failed_count += 1
            
            return orders_data
            
        except Exception as e:
            logger.error(f"❌ Error syncing Daraz orders: {e}")
            return orders_data
    
    def _get_order_detail(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed order information"""
        params = {'order_id': order_id}
        response = self._make_request('/order/get', params)
        
        if response and 'data' in response:
            return response['data']
        
        return None
    
    def _transform_order(self, order: Dict[str, Any], item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transform Daraz order to our schema
        
        Args:
            order: Daraz order details
            item: Order line item
            
        Returns:
            Transformed order dictionary
        """
        try:
            # Map Daraz status to our status
            status_mapping = {
                'pending': 'pending',
                'ready_to_ship': 'confirmed',
                'shipped': 'shipped',
                'delivered': 'delivered',
                'canceled': 'cancelled',
                'returned': 'cancelled',
                'failed': 'cancelled'
            }
            
            order_status = status_mapping.get(
                order.get('status', '').lower(),
                'pending'
            )
            
            # Extract shipping region
            address = order.get('address_shipping', {})
            shipping_region = address.get('city') or address.get('region')
            
            # Build order data
            order_data = {
                "order_id": f"DARAZ-{order['order_id']}-{item['order_item_id']}",
                "platform": "daraz",
                "customer_id": str(order.get('customer_id', 'unknown')),
                "customer_email_hash": self._hash_email(order.get('customer_email')) if order.get('customer_email') else None,
                "product_id": str(item['sku']),
                "product_name": item['name'],
                "product_category": item.get('product_main_category', 'Uncategorized'),
                "quantity": int(item['quantity']),
                "unit_price": float(item['item_price']),
                "total_price": float(item['paid_price']),
                "currency": "BDT",
                "order_status": order_status,
                "payment_method": order.get('payment_method'),
                "shipping_region": shipping_region,
                "order_timestamp": order['created_at'],
                "updated_at": order.get('updated_at', datetime.utcnow().isoformat())
            }
            
            return order_data
            
        except Exception as e:
            logger.error(f"❌ Error transforming order: {e}")
            return None
    
    def _hash_email(self, email: str) -> str:
        """Hash email for privacy"""
        return hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    
    def _send_to_kafka(self, order_data: Dict[str, Any]) -> bool:
        """Validate and send order to Kafka"""
        # Validate against Pydantic schema
        is_valid, validated_model, error = validate_market_order(order_data)
        
        if not is_valid:
            logger.warning(f"⚠️  Schema validation failed: {error}")
            # Send to DLQ
            try:
                send_to_market_dlq(
                    data=order_data,
                    error=ValueError(error),
                    source_topic="source.market.daraz",
                    additional_context={"integration": "daraz", "validation": "pydantic"}
                )
            except Exception as dlq_error:
                logger.error(f"❌ Failed to send to DLQ: {dlq_error}")
            return False
        
        # Send validated data to Kafka
        try:
            success = self.producer.send_message(validated_model.model_dump())
            if success:
                logger.info(f"✅ Order {order_data['order_id']} sent to Kafka")
            return success
        except Exception as e:
            logger.error(f"❌ Kafka send failed: {e}")
            return False
    
    def run_sync(self, limit: int = 100):
        """
        Run full order synchronization
        
        Args:
            limit: Maximum orders to sync
        """
        logger.info("🚀 Starting Daraz order sync")
        
        try:
            # Sync different order statuses
            statuses = ['pending', 'ready_to_ship', 'shipped']
            all_orders = []
            
            for status in statuses:
                logger.info(f"\n📦 Syncing '{status}' orders...")
                orders = self.sync_orders(limit=limit // len(statuses), status=status)
                all_orders.extend(orders)
            
            # Send to Kafka
            for order in all_orders:
                self._send_to_kafka(order)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Sync complete!")
            logger.info(f"   Successfully synced: {self.scraped_count}")
            logger.info(f"   Failed: {self.failed_count}")
            logger.info('='*60)
            
        except Exception as e:
            logger.error(f"❌ Critical error in Daraz sync: {e}")
            raise
        finally:
            self.producer.close()


def main():
    """Entry point for Daraz integration"""
    try:
        integration = DarazIntegration()
        integration.run_sync()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Set DARAZ_APP_KEY and DARAZ_APP_SECRET environment variables")


if __name__ == "__main__":
    main()
