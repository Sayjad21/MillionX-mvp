"""
Quick Kafka to Snowflake - Process existing messages and exit
"""

import os
import sys
from dotenv import load_dotenv
from kafka import KafkaConsumer
import snowflake.connector
import json
from datetime import datetime

load_dotenv('../.env')

print("Processing Kafka messages to Snowflake...")

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    database='MILLIONX',
    schema='RAW_DATA'
)
cursor = conn.cursor()
print("✅ Snowflake connected")

# Connect to Kafka with timeout
consumer = KafkaConsumer(
    'source.social.tiktok',
    'source.social.facebook',
    'source.market.shopify',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    consumer_timeout_ms=5000,  # Exit after 5 seconds of no messages
    group_id='snowflake-quick-test'
)
print("✅ Kafka connected\n")

processed = 0
for message in consumer:
    data = message.value
    topic = message.topic
    
    try:
        if 'social' in topic:
            cursor.execute("""
                INSERT INTO SOCIAL_POSTS (
                    post_id, platform, content, author, engagement_count,
                    likes_count, comments_count, shares_count, post_url,
                    hashtags, location, posted_at, ingestion_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('post_id'), data.get('platform'), data.get('content'),
                data.get('author_handle'), data.get('engagement_count', 0),
                data.get('likes_count', 0), data.get('comments_count', 0),
                data.get('shares_count', 0), data.get('post_url'),
                json.dumps(data.get('hashtags', [])), data.get('location'),
                data.get('posted_at'), datetime.now()
            ))
            print(f"✓ Social: {data.get('post_id')}")
            
        elif 'market' in topic:
            cursor.execute("""
                INSERT INTO MARKET_ORDERS (
                    order_id, merchant_id, product_id, product_name,
                    product_category, quantity, unit_price, total_amount,
                    currency, customer_id, customer_location, payment_method,
                    order_status, timestamp, ingestion_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('order_id'), data.get('merchant_id'), data.get('product_id'),
                data.get('product_name'), data.get('product_category'),
                data.get('quantity'), data.get('unit_price'), data.get('total_amount'),
                data.get('currency', 'BDT'), data.get('customer_id'),
                data.get('customer_location'), data.get('payment_method'),
                data.get('order_status'), data.get('timestamp'), datetime.now()
            ))
            print(f"✓ Market: {data.get('order_id')}")
        
        conn.commit()
        processed += 1
    except Exception as e:
        print(f"⚠️  Error: {e}")
        conn.rollback()

print(f"\n✅ Processed {processed} messages\n")

# Verify
cursor.execute("SELECT COUNT(*) FROM SOCIAL_POSTS")
social = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM MARKET_ORDERS")
market = cursor.fetchone()[0]

print(f"Snowflake Tables:")
print(f"  SOCIAL_POSTS: {social} rows")
print(f"  MARKET_ORDERS: {market} rows")

cursor.close()
conn.close()
consumer.close()
print("\n✅ Complete!")
