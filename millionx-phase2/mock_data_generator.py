"""
Mock Data Generator for Phase 2 Pipeline Testing
Generates realistic test data without requiring paid APIs

Usage:
    python mock_data_generator.py

Features:
- Generates social media posts (TikTok/Facebook style)
- Generates e-commerce orders (Shopify style)
- Includes mock weather data
- Sends data directly to Kafka topics
- No external APIs required
"""

import json
import random
import time
from datetime import datetime, timedelta, timezone
from kafka import KafkaProducer
import hashlib
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
NUM_SOCIAL_POSTS = 100
NUM_ORDERS = 150

print("=" * 80)
print("🎭 MOCK DATA GENERATOR FOR MILLIONX PHASE 2")
print("=" * 80)
print()
print("📊 Configuration:")
print(f"   Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
print(f"   Social Posts: {NUM_SOCIAL_POSTS}")
print(f"   Orders: {NUM_ORDERS}")
print()

# ============================================================================
# MOCK DATA TEMPLATES
# ============================================================================

PRODUCT_CATEGORIES = {
    'smartphone': [
        'iPhone 15 Pro Max', 'Samsung Galaxy S24', 'Xiaomi Redmi Note 13',
        'OnePlus 12', 'Google Pixel 8', 'Vivo V30', 'Oppo Reno 11',
        'Realme 11 Pro', 'Nothing Phone 2', 'Honor Magic 6'
    ],
    'laptop': [
        'MacBook Pro M3', 'Dell XPS 15', 'HP Pavilion', 'Lenovo ThinkPad',
        'Asus ROG', 'Acer Aspire', 'MSI Gaming Laptop',
        'Surface Laptop 5', 'Razer Blade 15', 'LG Gram'
    ],
    'wearables': [
        'Apple Watch Series 9', 'Samsung Galaxy Watch 6', 'Fitbit Charge 6',
        'Garmin Forerunner 955', 'Amazfit GTR 4', 'Xiaomi Mi Band 8'
    ],
    'tablets': [
        'iPad Pro M2', 'Samsung Galaxy Tab S9', 'Microsoft Surface Pro 9',
        'Lenovo Tab P12', 'Xiaomi Pad 6', 'Amazon Fire HD 10'
    ],
    'gaming': [
        'PlayStation 5', 'Xbox Series X', 'Nintendo Switch OLED',
        'Steam Deck', 'Meta Quest 3', 'Asus ROG Ally'
    ],
    'fashion': [
        'Nike Air Max', 'Adidas Ultraboost', 'Zara Dress', 'H&M Jacket',
        'Levis Jeans', 'Puma Sneakers', 'Gucci Bag', 'Ray-Ban Sunglasses'
    ],
    'electronics': [
        'Sony WH-1000XM5', 'AirPods Pro', 'Samsung TV 55"', 'Canon EOS R6', 
        'DJI Drone', 'Bose SoundLink', 'JBL Flip 6'
    ],
    'home': [
        'Philips Air Fryer', 'Dyson Vacuum', 'Samsung Refrigerator',
        'LG Washing Machine', 'Instant Pot', 'KitchenAid Mixer'
    ]
}

SOCIAL_CONTENT_TEMPLATES = [
    "Amazing {product} for sale! 🔥 Only {price} Taka. Contact me for details!",
    "Just got this {product} and it's incredible! 😍 Best purchase ever!",
    "Looking for a {product}? I have one in perfect condition! DM me.",
    "SALE ALERT! {product} at {price} Taka only! Limited stock! 🚨",
    "{product} review: 10/10! Worth every penny at {price} Taka.",
    "Who wants a {product}? Brand new, sealed! {price} Taka negotiable.",
    "Unboxing my new {product}! Can't believe I got it for {price} Taka! 📦",
    "{product} comparison: This one is the best! Only {price} Taka!"
]

BANGLADESH_CITIES = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna', 'Barisal', 'Rangpur', 'Mymensingh']
WEATHER_CONDITIONS = ['Clear', 'Clouds', 'Rain', 'Drizzle', 'Thunderstorm', 'Mist']

FIRST_NAMES = ['Mohammad', 'Abdul', 'Fatima', 'Ayesha', 'Karim', 'Nadia', 'Rahim', 'Sadia', 'Hasan', 'Sultana']
LAST_NAMES = ['Rahman', 'Ahmed', 'Khan', 'Hossain', 'Islam', 'Akter', 'Begum', 'Chowdhury', 'Ali', 'Mia']

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_phone():
    """Generate fake Bangladesh phone number"""
    return f"+8801{random.randint(700000000, 799999999)}"

def generate_email(name):
    """Generate fake email"""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    return f"{name.lower().replace(' ', '.')}{random.randint(1, 999)}@{random.choice(domains)}"

def generate_hash(text):
    """Generate SHA-256 hash (first 16 chars)"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def random_date(days_ago=30):
    """Generate random datetime within last N days"""
    now = datetime.now(timezone.utc)
    delta = timedelta(days=random.randint(0, days_ago), 
                      hours=random.randint(0, 23),
                      minutes=random.randint(0, 59))
    return (now - delta).isoformat() + 'Z'

def get_random_product():
    """Get random product with category"""
    category = random.choice(list(PRODUCT_CATEGORIES.keys()))
    product = random.choice(PRODUCT_CATEGORIES[category])
    price = random.randint(5000, 150000)
    return category, product, price

def get_mock_weather():
    """Generate mock weather data"""
    return {
        'condition': random.choice(WEATHER_CONDITIONS),
        'temperature': random.randint(15, 38),
        'humidity': random.randint(40, 90),
        'wind_speed': round(random.uniform(2.0, 15.0), 1),
        'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'light rain', 'heavy rain'])
    }

# ============================================================================
# DATA GENERATORS
# ============================================================================

def generate_social_post():
    """Generate realistic social media post"""
    category, product, price = get_random_product()
    platform = random.choice(['tiktok', 'facebook'])
    
    # Create post content with potential PII
    content_template = random.choice(SOCIAL_CONTENT_TEMPLATES)
    content = content_template.format(product=product, price=price)
    
    # Randomly add contact info (for Privacy Shield to detect)
    if random.random() < 0.3:  # 30% chance
        phone = generate_phone()
        content += f" Contact: {phone}"
    
    if random.random() < 0.2:  # 20% chance
        email = generate_email("user")
        content += f" Email: {email}"
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    author_name = f"{first_name} {last_name}"
    
    post = {
        "post_id": f"mock_{platform}_{random.randint(100000, 999999)}",
        "platform": platform,
        "content": content,
        "author_handle": f"@{first_name.lower()}{random.randint(1, 999)}",
        "author_name": author_name,  # Will be anonymized by Privacy Shield
        "engagement_count": random.randint(100, 50000),
        "likes_count": random.randint(50, 20000),
        "comments_count": random.randint(10, 5000),
        "shares_count": random.randint(5, 2000),
        "post_url": f"https://{platform}.com/mock/{random.randint(1000, 9999)}",
        "hashtags": [category, 'sale', 'bangladesh', random.choice(['dhaka', 'deals', 'shopping'])],
        "location": random.choice(BANGLADESH_CITIES),
        "timestamp": random_date(days_ago=7)
    }
    
    return post

def generate_market_order():
    """Generate realistic e-commerce order"""
    category, product, price = get_random_product()
    quantity = random.randint(1, 5)
    total_price = price * quantity
    
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    customer_name = f"{first_name} {last_name}"
    customer_phone = generate_phone()
    customer_email = generate_email(customer_name)
    
    order = {
        "order_id": f"ORD-{random.randint(10000, 99999)}",
        "platform": random.choice(['shopify', 'daraz']),
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "customer_phone": customer_phone,  # Will be hashed by Privacy Shield
        "customer_email": customer_email,  # Will be hashed by Privacy Shield
        "customer_name": customer_name,    # Will be anonymized
        "product_id": f"PROD-{random.randint(100, 999)}",
        "product_name": product,
        "product_category": category,
        "quantity": quantity,
        "unit_price": price,
        "total_price": total_price,
        "currency": "BDT",
        "order_status": random.choice(['confirmed', 'pending', 'shipped', 'delivered']),
        "payment_method": random.choice(['COD', 'bKash', 'Nagad', 'Card']),
        "shipping_region": random.choice(BANGLADESH_CITIES),
        "shipping_city": random.choice(BANGLADESH_CITIES),
        "timestamp": random_date(days_ago=30)
    }
    
    return order

def generate_weather_data(city):
    """Generate weather data for a city"""
    weather = get_mock_weather()
    
    data = {
        "city": city,
        "country": "BD",
        "temperature": weather['temperature'],
        "humidity": weather['humidity'],
        "conditions": weather['condition'],
        "description": weather['description'],
        "wind_speed": weather['wind_speed'],
        "timestamp": datetime.now(timezone.utc).isoformat() + 'Z'
    }
    
    return data

# ============================================================================
# KAFKA PRODUCER
# ============================================================================

print("📡 Connecting to Kafka...")
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
    print("✅ Connected to Kafka successfully!")
    print()
except Exception as e:
    print(f"❌ Failed to connect to Kafka: {e}")
    print("\n💡 Make sure Kafka is running:")
    print("   cd millionx-phase2")
    print("   docker-compose -f docker-compose.kafka.yml up -d")
    exit(1)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 80)
    print("📤 SENDING MOCK DATA TO KAFKA")
    print("=" * 80)
    print()
    
    # 1. Send Social Posts
    print(f"1️⃣  Generating {NUM_SOCIAL_POSTS} social media posts...")
    social_success = 0
    for i in range(NUM_SOCIAL_POSTS):
        try:
            post = generate_social_post()
            topic = f"source.social.{post['platform']}"
            producer.send(topic, post)
            social_success += 1
            
            if (i + 1) % 20 == 0:
                print(f"   ✓ Sent {i + 1}/{NUM_SOCIAL_POSTS} posts...")
        except Exception as e:
            print(f"   ✗ Failed to send post {i+1}: {e}")
    
    producer.flush()
    print(f"✅ Successfully sent {social_success}/{NUM_SOCIAL_POSTS} social posts")
    print()
    
    # 2. Send Market Orders
    print(f"2️⃣  Generating {NUM_ORDERS} e-commerce orders...")
    order_success = 0
    for i in range(NUM_ORDERS):
        try:
            order = generate_market_order()
            topic = f"source.market.{order['platform']}"
            producer.send(topic, order)
            order_success += 1
            
            if (i + 1) % 10 == 0:
                print(f"   ✓ Sent {i + 1}/{NUM_ORDERS} orders...")
        except Exception as e:
            print(f"   ✗ Failed to send order {i+1}: {e}")
    
    producer.flush()
    print(f"✅ Successfully sent {order_success}/{NUM_ORDERS} orders")
    print()
    
    # 3. Send Weather Data
    print(f"3️⃣  Generating weather data for {len(BANGLADESH_CITIES)} cities...")
    weather_success = 0
    for city in BANGLADESH_CITIES:
        try:
            weather = generate_weather_data(city)
            producer.send('context.weather', weather)
            weather_success += 1
        except Exception as e:
            print(f"   ✗ Failed to send weather for {city}: {e}")
    
    producer.flush()
    print(f"✅ Successfully sent {weather_success}/{len(BANGLADESH_CITIES)} weather records")
    print()
    
    # Close producer
    producer.close()
    
    # Summary
    print("=" * 80)
    print("🎉 MOCK DATA GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("📊 Summary:")
    print(f"   Social Posts: {social_success}/{NUM_SOCIAL_POSTS}")
    print(f"   Market Orders: {order_success}/{NUM_ORDERS}")
    print(f"   Weather Records: {weather_success}/{len(BANGLADESH_CITIES)}")
    print()
    print("🔍 Next Steps:")
    print("   1. Check Kafka UI: http://localhost:8080")
    print("   2. View topics: source.social.tiktok, source.market.shopify")
    print("   3. Watch stream processors process the data")
    print("   4. Query results in Snowflake or Weaviate")
    print()
    print("💡 To generate more data, just run this script again!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Closing producer...")
        producer.close()
        print("✅ Producer closed. Exiting.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
