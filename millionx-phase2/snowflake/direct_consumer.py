"""
Direct Kafka to Snowflake Consumer - Simplified for Testing
Consumes messages from Kafka and inserts into Snowflake
"""

import os
import sys
from dotenv import load_dotenv
from kafka import KafkaConsumer
import snowflake.connector
import json
from datetime import datetime
import time

# Load environment
load_dotenv('../.env')

print("=" * 70)
print("Kafka → Snowflake Direct Consumer")
print("=" * 70)
print()

# Connect to Snowflake
print("📡 Connecting to Snowflake...")
try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        database='MILLIONX',
        schema='RAW_DATA'
    )
    cursor = conn.cursor()
    print("✅ Connected to Snowflake")
except Exception as e:
    print(f"❌ Snowflake connection failed: {e}")
    sys.exit(1)

# Connect to Kafka
print("📡 Connecting to Kafka...")
try:
    consumer = KafkaConsumer(
        'source.social.tiktok',
        'source.social.facebook',
        'source.market.shopify',
        'source.market.daraz',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='snowflake-direct-consumer'
    )
    print("✅ Connected to Kafka")
except Exception as e:
    print(f"❌ Kafka connection failed: {e}")
    sys.exit(1)

print()
print("🔄 Processing messages (Ctrl+C to stop)...")
print()

processed = 0
social_count = 0
market_count = 0

try:
    for message in consumer:
        topic = message.topic
        data = message.value
        
        try:
            if 'social' in topic:
                # Insert into SOCIAL_POSTS
                sql = """
                INSERT INTO SOCIAL_POSTS (
                    post_id, platform, content, author, engagement_count,
                    likes_count, comments_count, shares_count, post_url,
                    hashtags, location, posted_at, ingestion_time
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                cursor.execute(sql, (
                    data.get('post_id'),
                    data.get('platform'),
                    data.get('content'),
                    data.get('author_handle'),
                    data.get('engagement_count', 0),
                    data.get('likes_count', 0),
                    data.get('comments_count', 0),
                    data.get('shares_count', 0),
                    data.get('post_url'),
                    json.dumps(data.get('hashtags', [])),
                    data.get('location'),
                    data.get('posted_at'),
                    datetime.now()
                ))
                
                social_count += 1
                print(f"✓ Social post: {data.get('post_id')} → SOCIAL_POSTS")
                
            elif 'market' in topic:
                # Insert into MARKET_ORDERS
                sql = """
                INSERT INTO MARKET_ORDERS (
                    order_id, merchant_id, product_id, product_name,
                    product_category, quantity, unit_price, total_amount,
                    currency, customer_id, customer_location, payment_method,
                    order_status, timestamp, ingestion_time
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                cursor.execute(sql, (
                    data.get('order_id'),
                    data.get('merchant_id'),
                    data.get('product_id'),
                    data.get('product_name'),
                    data.get('product_category'),
                    data.get('quantity'),
                    data.get('unit_price'),
                    data.get('total_amount'),
                    data.get('currency', 'BDT'),
                    data.get('customer_id'),
                    data.get('customer_location'),
                    data.get('payment_method'),
                    data.get('order_status'),
                    data.get('timestamp'),
                    datetime.now()
                ))
                
                market_count += 1
                print(f"✓ Market order: {data.get('order_id')} → MARKET_ORDERS")
            
            conn.commit()
            processed += 1
            
            # Stop after processing all available messages (for testing)
            if processed >= 3:
                print()
                print("✅ Processed all test messages!")
                break
                
        except Exception as e:
            print(f"⚠️  Error processing message: {e}")
            conn.rollback()
            
except KeyboardInterrupt:
    print("\n\n⏹️  Stopped by user")

finally:
    print()
    print("=" * 70)
    print("Processing Summary")
    print("=" * 70)
    print(f"Total processed: {processed} messages")
    print(f"Social posts: {social_count}")
    print(f"Market orders: {market_count}")
    print()
    
    # Verify data in Snowflake
    print("📊 Verifying data in Snowflake...")
    cursor.execute("SELECT COUNT(*) FROM SOCIAL_POSTS")
    print(f"  SOCIAL_POSTS: {cursor.fetchone()[0]} rows")
    
    cursor.execute("SELECT COUNT(*) FROM MARKET_ORDERS")
    print(f"  MARKET_ORDERS: {cursor.fetchone()[0]} rows")
    
    cursor.close()
    conn.close()
    consumer.close()
    
    print()
    print("✅ Consumer stopped")
