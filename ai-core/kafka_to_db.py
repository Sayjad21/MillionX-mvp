"""
Kafka to Database Bridge Consumer
Syncs market orders and social posts from Kafka to Postgres

Usage:
    python kafka_to_db.py

Author: MillionX Team
Phase: 3 (AI Core - Data Sync)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaConsumer
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///millionx_ai.db')
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_datetime(timestamp_str: str) -> datetime:
    """Parse datetime string, handling double timezone suffixes from mock data"""
    if not timestamp_str:
        return datetime.now()
    
    # Handle double timezone (+00:00+00:00 from mock data)
    if timestamp_str.count('+00:00') > 1:
        # Remove the duplicate timezone
        timestamp_str = timestamp_str.replace('+00:00+00:00', '+00:00')
    
    # Replace Z with +00:00
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # Fallback: try without timezone
        return datetime.fromisoformat(timestamp_str.split('+')[0])


# ============================================================================
# DATABASE MODELS
# ============================================================================

class SalesHistory(Base):
    """Sales history table for forecasting"""
    __tablename__ = 'sales_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(255), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    product_id = Column(String(255), nullable=False, index=True)
    product_name = Column(String(500))
    product_category = Column(String(100), index=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    total_price = Column(Float)
    currency = Column(String(10), default='BDT')
    order_status = Column(String(50))
    payment_method = Column(String(50))
    shipping_region = Column(String(255))
    shipping_city = Column(String(255), index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class SocialSignals(Base):
    """Social media signals table for trend analysis"""
    __tablename__ = 'social_signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    content = Column(Text)
    author_handle = Column(String(255))
    engagement_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    hashtags = Column(Text)  # JSON array as text
    location = Column(String(255), index=True)
    posted_at = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables created/verified")


# ============================================================================
# KAFKA CONSUMER
# ============================================================================

class KafkaToDatabaseBridge:
    """
    Consumes messages from Kafka topics and inserts into Postgres
    """
    
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.consumer = None
        self.session = SessionLocal()
        
        # Statistics
        self.orders_processed = 0
        self.posts_processed = 0
        self.errors = 0
    
    def start(self):
        """Initialize and start consuming"""
        logger.info("🚀 Starting Kafka to Database Bridge...")
        
        try:
            # Create consumer
            self.consumer = KafkaConsumer(
                'source.market.shopify',
                'source.market.daraz',
                'source.social.tiktok',
                'source.social.facebook',
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='ai-core-data-sync',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            logger.info(f"✅ Connected to Kafka: {self.bootstrap_servers}")
            logger.info(f"📥 Subscribed to topics: {self.consumer.subscription()}")
            logger.info("⏳ Waiting for messages...")
            
            # Consume messages
            for message in self.consumer:
                self.process_message(message)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Shutting down gracefully...")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            self.shutdown()
    
    def process_message(self, message):
        """Process a single Kafka message"""
        try:
            topic = message.topic
            data = message.value
            
            if 'market' in topic:
                self.process_order(data)
            elif 'social' in topic:
                self.process_post(data)
            else:
                logger.warning(f"Unknown topic: {topic}")
                
        except Exception as e:
            self.errors += 1
            logger.error(f"❌ Error processing message: {e}")
    
    def process_order(self, data: Dict[str, Any]):
        """Insert order into sales_history table"""
        try:
            # Check if already exists
            existing = self.session.query(SalesHistory).filter_by(
                order_id=data.get('order_id')
            ).first()
            
            if existing:
                logger.debug(f"Order {data.get('order_id')} already exists, skipping")
                return
            
            # Parse timestamp
            order_date = data.get('timestamp')
            if isinstance(order_date, str):
                order_date = parse_datetime(order_date)
            
            # Create record
            order = SalesHistory(
                order_id=data.get('order_id'),
                platform=data.get('platform'),
                product_id=data.get('product_id', 'unknown'),
                product_name=data.get('product_name'),
                product_category=data.get('product_category', 'general'),
                quantity=data.get('quantity', 1),
                unit_price=data.get('unit_price', 0),
                total_price=data.get('total_price', 0),
                currency=data.get('currency', 'BDT'),
                order_status=data.get('order_status', 'pending'),
                payment_method=data.get('payment_method', 'unknown'),
                shipping_region=data.get('shipping_region'),
                shipping_city=data.get('shipping_city'),
                order_date=order_date
            )
            
            self.session.add(order)
            self.session.commit()
            
            self.orders_processed += 1
            if self.orders_processed % 10 == 0:
                logger.info(f"📦 Orders processed: {self.orders_processed}")
                
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error processing order: {e}")
    
    def process_post(self, data: Dict[str, Any]):
        """Insert post into social_signals table"""
        try:
            # Check if already exists
            existing = self.session.query(SocialSignals).filter_by(
                post_id=data.get('post_id')
            ).first()
            
            if existing:
                logger.debug(f"Post {data.get('post_id')} already exists, skipping")
                return
            
            # Parse timestamp
            posted_at = data.get('timestamp')
            if isinstance(posted_at, str):
                posted_at = parse_datetime(posted_at)
            
            # Create record
            post = SocialSignals(
                post_id=data.get('post_id'),
                platform=data.get('platform'),
                content=data.get('content'),
                author_handle=data.get('author_handle'),
                engagement_count=data.get('engagement_count', 0),
                likes_count=data.get('likes_count', 0),
                comments_count=data.get('comments_count', 0),
                shares_count=data.get('shares_count', 0),
                hashtags=json.dumps(data.get('hashtags', [])),
                location=data.get('location'),
                posted_at=posted_at
            )
            
            self.session.add(post)
            self.session.commit()
            
            self.posts_processed += 1
            if self.posts_processed % 10 == 0:
                logger.info(f"📱 Posts processed: {self.posts_processed}")
                
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error processing post: {e}")
    
    def shutdown(self):
        """Cleanup and close connections"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Orders processed: {self.orders_processed}")
        logger.info(f"Posts processed: {self.posts_processed}")
        logger.info(f"Errors: {self.errors}")
        logger.info("=" * 70)
        
        if self.consumer:
            self.consumer.close()
        
        self.session.close()
        logger.info("✅ Bridge shutdown complete")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    bridge = KafkaToDatabaseBridge()
    bridge.start()
