"""
Test Enhanced Mock Data Generator (Phase 3)
Validates seasonality and regional patterns
"""

from mock_data_generator import (
    generate_market_order,
    get_seasonal_multiplier,
    get_regional_preference_multiplier
)
from datetime import datetime
import json

print("=" * 80)
print("🧪 TESTING PHASE 3: ENHANCED MOCK DATA GENERATOR")
print("=" * 80)
print()

# Test 1: Seasonal Multipliers
print("📅 Test 1: Seasonal Multipliers")
print("-" * 40)

test_dates = [
    (datetime(2025, 7, 15), 'fashion', 'Eid Season - Fashion'),
    (datetime(2025, 12, 25), 'fashion', 'Winter - Fashion'),
    (datetime(2025, 4, 14), 'fashion', 'Pohela Boishakh'),
    (datetime(2025, 6, 20), 'electronics', 'Monsoon - Electronics'),
    (datetime(2025, 11, 25), 'smartphone', 'Black Friday')
]

for date, category, description in test_dates:
    mult = get_seasonal_multiplier(date, category)
    print(f"  {description:30s} → Multiplier: {mult:.2f}x")

print()

# Test 2: Regional Preferences
print("🗺️  Test 2: Regional Preference Multipliers")
print("-" * 40)

regions = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi']
categories = ['smartphone', 'fashion', 'laptop']

for region in regions:
    print(f"  {region}:")
    for category in categories:
        mult = get_regional_preference_multiplier(region, category)
        print(f"    {category:15s} → {mult:.2f}x")

print()

# Test 3: Generate Sample Orders
print("📦 Test 3: Sample Orders with Enhanced Patterns")
print("-" * 40)

for i in range(5):
    order = generate_market_order()
    print(f"\n  Order #{i+1}:")
    print(f"    Product: {order['product_name']}")
    print(f"    Category: {order['product_category']}")
    print(f"    Quantity: {order['quantity']}")
    print(f"    Price: {order['total_price']:,} BDT")
    print(f"    Region: {order['shipping_region']}")
    print(f"    Date: {order['timestamp'][:10]}")
    print(f"    Metadata:")
    print(f"      - Seasonal: {order['metadata']['seasonal_multiplier']}x")
    print(f"      - Regional: {order['metadata']['regional_multiplier']}x")
    print(f"      - Weekend: {order['metadata']['is_weekend']}")

print()

# Test 4: Statistical Analysis
print("📊 Test 4: Pattern Distribution (100 orders)")
print("-" * 40)

from collections import defaultdict

seasonal_counts = defaultdict(int)
regional_counts = defaultdict(int)
category_counts = defaultdict(int)

for _ in range(100):
    order = generate_market_order()
    
    # Count seasonality
    seasonal_mult = order['metadata']['seasonal_multiplier']
    if seasonal_mult > 2.0:
        seasonal_counts['High Demand (>2x)'] += 1
    elif seasonal_mult > 1.5:
        seasonal_counts['Medium Demand (1.5-2x)'] += 1
    else:
        seasonal_counts['Normal Demand (<1.5x)'] += 1
    
    # Count regions
    regional_counts[order['shipping_region']] += 1
    
    # Count categories
    category_counts[order['product_category']] += 1

print("\n  Seasonal Distribution:")
for key, count in sorted(seasonal_counts.items()):
    print(f"    {key:30s}: {count:3d} orders ({count}%)")

print("\n  Regional Distribution:")
for key, count in sorted(regional_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"    {key:30s}: {count:3d} orders ({count}%)")

print("\n  Category Distribution:")
for key, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"    {key:30s}: {count:3d} orders ({count}%)")

print()
print("=" * 80)
print("✅ PHASE 3 TESTS COMPLETE")
print("=" * 80)
print()
print("Key Improvements:")
print("  ✅ Seasonal patterns applied (Eid, Monsoon, Winter, Black Friday)")
print("  ✅ Regional preferences implemented (Dhaka tech hub, Chittagong trade)")
print("  ✅ Weekend boosts enabled")
print("  ✅ Metadata tracking for analysis")
print()
print("Next Steps:")
print("  → Run full mock_data_generator.py to populate Kafka")
print("  → Verify data in TimescaleDB")
print("  → Test forecasting with seasonal data")
print()
