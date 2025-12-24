"""
Populate TimescaleDB with data from PostgreSQL and generate additional records
"""
import os
import sys
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

# Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
TIMESCALE_HOST = os.getenv('TIMESCALE_HOST', 'localhost')
POSTGRES_PORT = 5432
TIMESCALE_PORT = 5433
USER = 'millionx'
PASSWORD = 'millionx_secure_2025'

# Product catalog
PRODUCTS = [
    ('PROD-001', 'iPhone 15 Pro Max', 'smartphone', 150000),
    ('PROD-002', 'Samsung Galaxy S24', 'smartphone', 120000),
    ('PROD-003', 'Xiaomi Redmi Note 13', 'smartphone', 35000),
    ('PROD-004', 'OnePlus 12', 'smartphone', 95000),
    ('PROD-005', 'Google Pixel 8', 'smartphone', 85000),
    ('PROD-011', 'MacBook Pro M3', 'laptop', 250000),
    ('PROD-012', 'Dell XPS 15', 'laptop', 180000),
    ('PROD-013', 'HP Pavilion', 'laptop', 75000),
    ('PROD-014', 'Lenovo ThinkPad', 'laptop', 120000),
    ('PROD-021', 'Apple Watch Series 9', 'wearables', 55000),
    ('PROD-022', 'Samsung Galaxy Watch 6', 'wearables', 35000),
    ('PROD-031', 'iPad Pro M2', 'tablets', 130000),
    ('PROD-032', 'Samsung Galaxy Tab S9', 'tablets', 85000),
    ('PROD-041', 'PlayStation 5', 'gaming', 75000),
    ('PROD-042', 'Xbox Series X', 'gaming', 65000),
    ('PROD-051', 'Nike Air Max', 'fashion', 15000),
    ('PROD-052', 'Adidas Ultraboost', 'fashion', 18000),
    ('PROD-061', 'Sony WH-1000XM5', 'electronics', 40000),
    ('PROD-062', 'AirPods Pro', 'electronics', 35000),
    ('PROD-071', 'Philips Air Fryer', 'home', 12000),
    ('PROD-072', 'Dyson Vacuum', 'home', 65000),
]

REGIONS = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna', 'Barisal', 'Rangpur', 'Mymensingh']
PAYMENT_METHODS = ['COD', 'bKash', 'Nagad', 'Card']

def get_seasonal_multiplier(date, category):
    """Get seasonal demand multiplier"""
    month = date.month
    day = date.day
    day_of_week = date.weekday()
    
    mult = 1.0
    
    # Eid season (July-August)
    if month in [7, 8]:
        if category == 'fashion':
            mult *= 2.5
        elif category in ['smartphone', 'electronics']:
            mult *= 1.8
    
    # Pohela Boishakh (April 14)
    if month == 4 and 10 <= day <= 18:
        mult *= 1.5
    
    # Winter (December-January)
    if month in [12, 1]:
        if category == 'fashion':
            mult *= 2.0
        elif category in ['electronics', 'home']:
            mult *= 1.4
    
    # Black Friday (late November)
    if month == 11 and 20 <= day <= 30:
        mult *= 2.0
    
    # Weekend boost
    if day_of_week in [4, 5]:  # Friday, Saturday
        mult *= 1.3
    
    return mult

def generate_order(date):
    """Generate a single order"""
    product = random.choice(PRODUCTS)
    product_id, product_name, category, base_price = product
    
    # Apply seasonal multiplier to quantity
    seasonal_mult = get_seasonal_multiplier(date, category)
    base_qty = random.randint(1, 5)
    quantity = max(1, int(base_qty * seasonal_mult * random.uniform(0.6, 1.4)))
    
    # Price with some variance
    unit_price = base_price * random.uniform(0.9, 1.1)
    total_amount = unit_price * quantity
    
    region = random.choice(REGIONS)
    payment = random.choice(PAYMENT_METHODS)
    merchant_id = f"MERCH-{random.randint(100, 999)}"
    order_id = f"ORD-{date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    return (
        order_id, product_id, product_name, category, quantity,
        round(unit_price, 2), round(total_amount, 2), date, region, merchant_id, payment
    )

def populate_timescale():
    """Populate TimescaleDB with 90 days of sales data"""
    print("=" * 60)
    print("📊 POPULATING TIMESCALEDB")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host=TIMESCALE_HOST,
            port=TIMESCALE_PORT,
            user=USER,
            password=PASSWORD,
            database='millionx_analytics'
        )
        cursor = conn.cursor()
        print("✅ Connected to TimescaleDB")
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sales_history'
            );
        """)
        if not cursor.fetchone()[0]:
            print("❌ Table sales_history does not exist!")
            return
        
        # Generate 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        records = []
        current_date = start_date
        
        print(f"📅 Generating data from {start_date.date()} to {end_date.date()}")
        
        while current_date <= end_date:
            # Generate 5-15 orders per day
            orders_per_day = random.randint(5, 15)
            
            for _ in range(orders_per_day):
                # Random time during the day
                order_time = current_date.replace(
                    hour=random.randint(8, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                records.append(generate_order(order_time))
            
            current_date += timedelta(days=1)
        
        print(f"📦 Generated {len(records)} orders")
        
        # Insert records
        insert_query = """
            INSERT INTO sales_history 
            (order_id, product_id, product_name, product_category, quantity, 
             unit_price, total_amount, order_date, customer_region, merchant_id, payment_method)
            VALUES %s
            ON CONFLICT (order_id) DO NOTHING
        """
        
        execute_values(cursor, insert_query, records)
        conn.commit()
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM sales_history")
        count = cursor.fetchone()[0]
        print(f"✅ TimescaleDB now has {count} records")
        
        cursor.close()
        conn.close()
        print("✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def add_to_postgres():
    """Add more records to PostgreSQL"""
    print("\n" + "=" * 60)
    print("📊 ADDING MORE DATA TO POSTGRESQL")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=USER,
            password=PASSWORD,
            database='millionx'
        )
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")
        
        # Get current count
        cursor.execute("SELECT COUNT(*) FROM sales_history")
        current_count = cursor.fetchone()[0]
        print(f"📦 Current records: {current_count}")
        
        # Generate 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        records = []
        current_date = start_date
        
        while current_date <= end_date:
            orders_per_day = random.randint(5, 15)
            
            for _ in range(orders_per_day):
                order_time = current_date.replace(
                    hour=random.randint(8, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                records.append(generate_order(order_time))
            
            current_date += timedelta(days=1)
        
        print(f"📦 Generated {len(records)} new orders")
        
        # Insert records
        insert_query = """
            INSERT INTO sales_history 
            (order_id, product_id, product_name, product_category, quantity, 
             unit_price, total_amount, order_date, customer_region, merchant_id, payment_method)
            VALUES %s
            ON CONFLICT (order_id) DO NOTHING
        """
        
        execute_values(cursor, insert_query, records)
        conn.commit()
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM sales_history")
        new_count = cursor.fetchone()[0]
        print(f"✅ PostgreSQL now has {new_count} records (+{new_count - current_count})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 DATABASE POPULATION SCRIPT")
    print("=" * 60)
    
    add_to_postgres()
    populate_timescale()
    
    print("\n" + "=" * 60)
    print("✅ ALL DONE!")
    print("=" * 60)
