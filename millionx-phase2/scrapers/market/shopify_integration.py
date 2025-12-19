"""
Shopify REST API Integration
Syncs orders and products from Shopify store
"""
import shopify
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
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


class ShopifyIntegration:
    """
    Shopify API client for syncing orders and inventory
    """
    
    def __init__(self):
        """Initialize Shopify API session"""
        self.shop_url = Config.SHOPIFY_SHOP_URL
        self.access_token = Config.SHOPIFY_ACCESS_TOKEN
        self.api_version = Config.SHOPIFY_API_VERSION
        
        if not self.shop_url or not self.access_token:
            raise ValueError("SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN must be configured")
        
        # Initialize Shopify session
        session = shopify.Session(
            self.shop_url,
            self.api_version,
            self.access_token
        )
        shopify.ShopifyResource.activate_session(session)
        
        self.producer = KafkaProducerClient("source.market.shopify")
        self.scraped_count = 0
        self.failed_count = 0
        
        logger.info(f"✅ Shopify session initialized for: {self.shop_url}")
    
    def sync_orders(
        self, 
        limit: int = 250,
        status: str = "any",
        created_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Sync orders from Shopify
        
        Args:
            limit: Maximum orders to fetch (max 250 per request)
            status: Order status filter ('open', 'closed', 'any')
            created_after: Only fetch orders after this datetime
            
        Returns:
            List of order dictionaries
        """
        orders_data = []
        
        logger.info(f"🔍 Syncing Shopify orders (limit: {limit}, status: {status})")
        
        try:
            # Build query parameters
            params = {
                'limit': min(limit, 250),  # Shopify max is 250
                'status': status
            }
            
            if created_after:
                params['created_at_min'] = created_after.isoformat()
            else:
                # Default: last 24 hours
                params['created_at_min'] = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Fetch orders
            orders = shopify.Order.find(**params)
            
            logger.info(f"📊 Found {len(orders)} orders from Shopify")
            
            # Transform orders
            for order in orders:
                try:
                    # Process each line item as a separate order record
                    for line_item in order.line_items:
                        order_data = self._transform_order(order, line_item)
                        if order_data:
                            orders_data.append(order_data)
                            self.scraped_count += 1
                except Exception as e:
                    logger.error(f"❌ Error transforming order {order.id}: {e}")
                    self.failed_count += 1
            
            return orders_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching Shopify orders: {e}")
            return orders_data
    
    def _transform_order(self, order, line_item) -> Optional[Dict[str, Any]]:
        """
        Transform Shopify order to our schema
        
        Args:
            order: Shopify Order object
            line_item: Shopify LineItem object
            
        Returns:
            Transformed order dictionary
        """
        try:
            # Map Shopify financial_status to our order_status
            status_mapping = {
                'pending': 'pending',
                'authorized': 'confirmed',
                'partially_paid': 'confirmed',
                'paid': 'confirmed',
                'partially_refunded': 'confirmed',
                'refunded': 'cancelled',
                'voided': 'cancelled'
            }
            
            order_status = status_mapping.get(
                order.financial_status, 
                'pending'
            )
            
            # If order is fulfilled, mark as delivered
            if order.fulfillment_status == 'fulfilled':
                order_status = 'delivered'
            elif order.fulfillment_status == 'partial':
                order_status = 'shipped'
            
            # Extract shipping region (from shipping_address)
            shipping_region = None
            if order.shipping_address:
                shipping_region = order.shipping_address.city or order.shipping_address.province
            
            # Build order data
            order_data = {
                "order_id": f"SHOPIFY-{order.id}-{line_item.id}",
                "platform": "shopify",
                "customer_id": str(order.customer.id) if order.customer else f"guest_{order.id}",
                "customer_email_hash": self._hash_email(order.email) if order.email else None,
                "product_id": str(line_item.product_id),
                "product_name": line_item.name,
                "product_category": line_item.product_type or "Uncategorized",
                "quantity": line_item.quantity,
                "unit_price": float(line_item.price),
                "total_price": float(line_item.price) * line_item.quantity,
                "currency": order.currency,
                "order_status": order_status,
                "payment_method": order.payment_gateway_names[0] if order.payment_gateway_names else None,
                "shipping_region": shipping_region,
                "order_timestamp": order.created_at,
                "updated_at": order.updated_at or datetime.utcnow().isoformat()
            }
            
            return order_data
            
        except Exception as e:
            logger.error(f"❌ Error transforming order: {e}")
            return None
    
    def _hash_email(self, email: str) -> str:
        """Hash email for privacy"""
        import hashlib
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
                    source_topic="source.market.shopify",
                    additional_context={"integration": "shopify", "validation": "pydantic"}
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
    
    def run_sync(self, limit: int = 250):
        """
        Run full order synchronization
        
        Args:
            limit: Maximum orders to sync
        """
        logger.info("🚀 Starting Shopify order sync")
        
        try:
            # Fetch orders
            orders = self.sync_orders(limit=limit)
            
            # Send to Kafka
            for order in orders:
                self._send_to_kafka(order)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Sync complete!")
            logger.info(f"   Successfully synced: {self.scraped_count}")
            logger.info(f"   Failed: {self.failed_count}")
            logger.info('='*60)
            
        except Exception as e:
            logger.error(f"❌ Critical error in Shopify sync: {e}")
            raise
        finally:
            shopify.ShopifyResource.clear_session()
            self.producer.close()


def main():
    """Entry point for Shopify integration"""
    try:
        integration = ShopifyIntegration()
        integration.run_sync()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Set SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN environment variables")


if __name__ == "__main__":
    main()
