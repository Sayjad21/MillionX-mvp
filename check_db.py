import sqlite3
import os

# Check both db locations
db_paths = [
    'ai-core/millionx_ai.db',
    'frontend/millionx_ai.db'
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"\n{'='*60}")
        print(f"Database: {db_path}")
        print('='*60)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTables: {[t[0] for t in tables]}")
        
        # Check sales_history
        if 'sales_history' in [t[0] for t in tables]:
            cursor.execute('SELECT COUNT(*) FROM sales_history')
            count = cursor.fetchone()[0]
            print(f"\nTotal sales records: {count}")
            
            # Get column names first
            cursor.execute('PRAGMA table_info(sales_history)')
            columns = cursor.fetchall()
            print(f"\nColumns: {[col[1] for col in columns]}")
            
            cursor.execute('SELECT DISTINCT product_id, product_name FROM sales_history LIMIT 30')
            products = cursor.fetchall()
            print(f"\nAvailable Products ({len(products)}):")
            for product_id, name in products:
                print(f"  {product_id}: {name}")
        
        conn.close()
    else:
        print(f"\n❌ Database not found: {db_path}")
