"""
SQLite to PostgreSQL Migration Script
Migrates data from SQLite (millionx_ai.db) to PostgreSQL

Usage:
    python migrate_sqlite_to_postgres.py
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Database URLs
SQLITE_DB = os.path.join(os.path.dirname(__file__), 'millionx_ai.db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'millionx')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'millionx_secure_2025')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'millionx')


def connect_sqlite():
    """Connect to SQLite database"""
    if not os.path.exists(SQLITE_DB):
        logger.warning(f"SQLite database not found: {SQLITE_DB}")
        return None
    
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    logger.info(f"✅ Connected to SQLite: {SQLITE_DB}")
    return conn


def connect_postgres():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        logger.info(f"✅ Connected to PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        raise


def migrate_sales_history(sqlite_conn, pg_conn):
    """Migrate sales_history table"""
    logger.info("📦 Migrating sales_history table...")
    
    # Fetch from SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM sales_history")
    rows = cursor.fetchall()
    
    if not rows:
        logger.warning("⚠️ No data found in sales_history table")
        return 0
    
    # Insert into PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    insert_query = """
        INSERT INTO sales_history 
        (order_id, product_id, product_name, product_category, quantity, 
         unit_price, total_amount, order_date, customer_region, merchant_id, 
         payment_method, ingested_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """
    
    data = [
        (
            row['order_id'],
            row['product_id'],
            row['product_name'],
            row['product_category'],
            row['quantity'],
            row['unit_price'] if 'unit_price' in row.keys() else None,
            row['total_amount'] if 'total_amount' in row.keys() else None,
            row['order_date'],
            row['customer_region'] if 'customer_region' in row.keys() else None,
            row['merchant_id'] if 'merchant_id' in row.keys() else None,
            row['payment_method'] if 'payment_method' in row.keys() else None,
            row['ingested_at'] if 'ingested_at' in row.keys() else datetime.now().isoformat()
        )
        for row in rows
    ]
    
    execute_batch(pg_cursor, insert_query, data, page_size=100)
    pg_conn.commit()
    
    logger.info(f"✅ Migrated {len(rows)} records to sales_history")
    return len(rows)


def migrate_social_signals(sqlite_conn, pg_conn):
    """Migrate social_signals table"""
    logger.info("📱 Migrating social_signals table...")
    
    # Check if table exists in SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='social_signals'
    """)
    
    if not cursor.fetchone():
        logger.warning("⚠️ social_signals table not found in SQLite")
        return 0
    
    cursor.execute("SELECT * FROM social_signals")
    rows = cursor.fetchall()
    
    if not rows:
        logger.warning("⚠️ No data found in social_signals table")
        return 0
    
    # Insert into PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    insert_query = """
        INSERT INTO social_signals 
        (platform, post_id, content, hashtags, engagement_score, 
         sentiment_score, product_mentions, author, posted_at, ingested_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (post_id) DO NOTHING
    """
    
    data = [
        (
            row['platform'],
            row['post_id'],
            row['content'],
            row['hashtags'].split(',') if ('hashtags' in row.keys() and row['hashtags']) else [],
            row['engagement_score'] if 'engagement_score' in row.keys() else 0,
            row['sentiment_score'] if 'sentiment_score' in row.keys() else None,
            row['product_mentions'].split(',') if ('product_mentions' in row.keys() and row['product_mentions']) else [],
            row['author'] if 'author' in row.keys() else None,
            row['posted_at'] if 'posted_at' in row.keys() else datetime.now().isoformat(),
            row['ingested_at'] if 'ingested_at' in row.keys() else datetime.now().isoformat()
        )
        for row in rows
    ]
    
    execute_batch(pg_cursor, insert_query, data, page_size=100)
    pg_conn.commit()
    
    logger.info(f"✅ Migrated {len(rows)} records to social_signals")
    return len(rows)


def update_env_file():
    """Update .env file to use PostgreSQL"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_file):
        logger.warning("⚠️ .env file not found, creating new one")
        with open(env_file, 'w') as f:
            f.write(f"DATABASE_URL=postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}\n")
    else:
        # Read existing content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add DATABASE_URL
        found = False
        for i, line in enumerate(lines):
            if line.startswith('DATABASE_URL='):
                lines[i] = f"DATABASE_URL=postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}\n"
                found = True
                break
        
        if not found:
            lines.append(f"\n# PostgreSQL Database\nDATABASE_URL=postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}\n")
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
    
    logger.info(f"✅ Updated .env file with PostgreSQL connection string")


def main():
    """Main migration function"""
    logger.info("=" * 70)
    logger.info("🔄 STARTING SQLITE TO POSTGRESQL MIGRATION")
    logger.info("=" * 70)
    
    # Connect to databases
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        logger.error("❌ Cannot proceed without SQLite database")
        logger.info("💡 Tip: Run the mock data generator first to create test data")
        return
    
    pg_conn = connect_postgres()
    
    try:
        # Migrate tables
        sales_count = migrate_sales_history(sqlite_conn, pg_conn)
        social_count = migrate_social_signals(sqlite_conn, pg_conn)
        
        # Update environment file
        update_env_file()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"📊 Total records migrated:")
        logger.info(f"   - Sales History: {sales_count}")
        logger.info(f"   - Social Signals: {social_count}")
        logger.info(f"   - Total: {sales_count + social_count}")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Test API: curl http://localhost:8000/health")
        logger.info("   2. Test forecast: curl http://localhost:8000/api/v1/inventory/forecast?limit=3")
        logger.info("   3. Check PostgreSQL: docker exec -it millionx-postgres psql -U millionx -d millionx -c 'SELECT COUNT(*) FROM sales_history;'")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
