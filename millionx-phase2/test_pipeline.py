"""
Phase 2 Pipeline Test - Send test data through Kafka to Snowflake
"""

import os
import sys
from dotenv import load_dotenv
from kafka import KafkaProducer
import json
from datetime import datetime
import time

# Load environment
load_dotenv('.env')

print("=" * 70)
print("Phase 2 Pipeline Test")
print("=" * 70)
print()

# Create Kafka producer
print("📡 Connecting to Kafka...")
try:
    producer = KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all'
    )
    print("✅ Connected to Kafka")
except Exception as e:
    print(f"❌ Failed to connect to Kafka: {e}")
    sys.exit(1)

print()
print("📤 Sending test data...")
print()

# Test 1: Social Post
social_post = {
    "post_id": "test_tiktok_001",
    "platform": "tiktok",
    "content": "Amazing new phone for sale! Contact me at john.doe@email.com or +8801712345678",
    "author_handle": "@testuser",
    "engagement_count": 1500,
    "likes_count": 1200,
    "comments_count": 250,
    "shares_count": 50,
    "post_url": "https://tiktok.com/test/001",
    "hashtags": ["phone", "sale", "dhaka"],
    "location": "Dhaka",
    "posted_at": datetime.now().isoformat(),
    "timestamp": datetime.now().isoformat()
}

print("1. Sending social post to source.social.tiktok...")
producer.send('source.social.tiktok', social_post)
print("   ✓ Sent: TikTok post with PII (should be anonymized)")

# Test 2: Market Order
market_order = {
    "order_id": "test_order_001",
    "merchant_id": "merchant_test_001",
    "product_id": "product_test_001",
    "product_name": "Test Smartphone",
    "product_category": "Electronics",
    "quantity": 2,
    "unit_price": 25000.00,
    "total_amount": 50000.00,
    "currency": "BDT",
    "customer_id": "customer_test_001",
    "customer_location": "Dhaka",
    "payment_method": "bKash",
    "order_status": "confirmed",
    "timestamp": datetime.now().isoformat()
}

print("2. Sending market order to source.market.shopify...")
producer.send('source.market.shopify', market_order)
print("   ✓ Sent: Shopify order")

# Test 3: Another social post
social_post2 = {
    "post_id": "test_facebook_001",
    "platform": "facebook",
    "content": "Best deals on laptops in Bangladesh! Free delivery in Dhaka",
    "author_handle": "TestShop",
    "engagement_count": 800,
    "likes_count": 650,
    "comments_count": 120,
    "shares_count": 30,
    "post_url": "https://facebook.com/test/001",
    "hashtags": ["laptop", "deals", "bangladesh"],
    "location": "Chittagong",
    "posted_at": datetime.now().isoformat(),
    "timestamp": datetime.now().isoformat()
}

print("3. Sending social post to source.social.facebook...")
producer.send('source.social.facebook', social_post2)
print("   ✓ Sent: Facebook post")

# Flush all messages
producer.flush()
print()
print("✅ All test messages sent to Kafka!")
print()

print("=" * 70)
print("Next Steps:")
print("=" * 70)
print()
print("1. Messages are now in Kafka topics")
print("2. Stream processors need to be started to process them")
print("3. Data will flow: Kafka → Stream Processors → Snowflake")
print()
print("To start stream processors:")
print("  cd stream-processors")
print("  pip install -r requirements.txt")
print("  faust -A privacy_shield worker -l info &")
print()
print("To verify data in Snowflake (after processing):")
print("  SELECT * FROM MILLIONX.RAW_DATA.SOCIAL_POSTS;")
print("  SELECT * FROM MILLIONX.RAW_DATA.MARKET_ORDERS;")
print()
print("Dashboards:")
print("  Kafka UI: http://localhost:8080")
print("  Grafana: http://localhost:3001")
print()

producer.close()
