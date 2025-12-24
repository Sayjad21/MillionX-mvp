"""
Generate SQL insert statements for PostgreSQL
"""
import random
from datetime import datetime, timedelta

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
    month = date.month
    day = date.day
    day_of_week = date.weekday()
    mult = 1.0
    if month in [7, 8]:
        if category == 'fashion': mult *= 2.5
        elif category in ['smartphone', 'electronics']: mult *= 1.8
    if month in [12, 1]:
        if category == 'fashion': mult *= 2.0
        elif category in ['electronics', 'home']: mult *= 1.4
    if month == 11 and 20 <= day <= 30: mult *= 2.0
    if day_of_week in [4, 5]: mult *= 1.3
    return mult

# Generate SQL
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

with open('insert_data.sql', 'w') as f:
    f.write("-- Auto-generated PostgreSQL insert statements\n\n")
    
    current_date = start_date
    record_count = 0
    
    while current_date <= end_date:
        orders_per_day = random.randint(5, 12)
        
        for _ in range(orders_per_day):
            order_time = current_date.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            product = random.choice(PRODUCTS)
            product_id, product_name, category, base_price = product
            
            seasonal_mult = get_seasonal_multiplier(order_time, category)
            quantity = max(1, int(random.randint(1, 5) * seasonal_mult * random.uniform(0.6, 1.4)))
            
            unit_price = round(base_price * random.uniform(0.9, 1.1), 2)
            total_amount = round(unit_price * quantity, 2)
            
            region = random.choice(REGIONS)
            payment = random.choice(PAYMENT_METHODS)
            merchant_id = f"MERCH-{random.randint(100, 999)}"
            order_id = f"ORD-{order_time.strftime('%Y%m%d%H%M%S')}-{random.randint(10000, 99999)}"
            
            # Use proper timestamp format for PostgreSQL
            timestamp = order_time.strftime('%Y-%m-%d %H:%M:%S')
            
            sql = f"""INSERT INTO sales_history (order_id, product_id, product_name, product_category, quantity, unit_price, total_amount, order_date, customer_region, merchant_id, payment_method) VALUES ('{order_id}', '{product_id}', '{product_name}', '{category}', {quantity}, {unit_price}, {total_amount}, '{timestamp}', '{region}', '{merchant_id}', '{payment}') ON CONFLICT DO NOTHING;\n"""
            f.write(sql)
            record_count += 1
        
        current_date += timedelta(days=1)
    
    print(f"Generated {record_count} INSERT statements in insert_data.sql")
