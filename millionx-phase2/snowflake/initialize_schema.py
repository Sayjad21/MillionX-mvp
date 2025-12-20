"""
Initialize Snowflake Database Schema for MillionX Phase 2
Run this to create the database, tables, indexes, and views
"""

import os
import sys
from dotenv import load_dotenv
import snowflake.connector

# Load environment variables
load_dotenv('../.env')

def initialize_snowflake_schema():
    """Create all Snowflake objects from schema-setup.sql"""
    
    print("=" * 60)
    print("MillionX Phase 2 - Snowflake Schema Initialization")
    print("=" * 60)
    print()
    
    # Connect to Snowflake
    print("📡 Connecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
        )
        print(f"✅ Connected as: {conn.user}")
        print(f"   Account: {conn.account}")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Read schema file
    print("📄 Reading schema-setup.sql...")
    try:
        with open('schema-setup.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print("✅ Schema file loaded")
        print()
    except Exception as e:
        print(f"❌ Failed to read schema file: {e}")
        conn.close()
        sys.exit(1)
    
    # Split SQL commands (handle multi-line statements)
    print("🔧 Executing SQL commands...")
    print()
    
    cursor = conn.cursor()
    
    # Split by semicolon, but keep comments
    commands = []
    current_command = []
    
    for line in sql_content.split('\n'):
        # Skip empty lines
        if not line.strip():
            continue
        
        # Skip comment-only lines
        if line.strip().startswith('--'):
            continue
            
        current_command.append(line)
        
        # Check if line ends with semicolon
        if line.strip().endswith(';'):
            full_command = '\n'.join(current_command)
            if full_command.strip() and not full_command.strip().startswith('--'):
                commands.append(full_command)
            current_command = []
    
    # Execute commands
    success_count = 0
    error_count = 0
    
    for i, cmd in enumerate(commands, 1):
        # Get first line for display
        first_line = cmd.split('\n')[0].strip()[:60]
        
        try:
            cursor.execute(cmd)
            
            # Print success message based on command type
            if 'CREATE DATABASE' in cmd.upper():
                print("✓ Database MILLIONX created")
            elif 'CREATE SCHEMA' in cmd.upper():
                print("✓ Schema RAW_DATA created")
            elif 'CREATE TABLE' in cmd.upper() and 'SOCIAL_POSTS' in cmd.upper():
                print("✓ Table SOCIAL_POSTS created")
            elif 'CREATE TABLE' in cmd.upper() and 'MARKET_ORDERS' in cmd.upper():
                print("✓ Table MARKET_ORDERS created")
            elif 'CREATE TABLE' in cmd.upper() and 'PRICE_HISTORY' in cmd.upper():
                print("✓ Table PRICE_HISTORY created")
            elif 'CREATE TABLE' in cmd.upper() and 'WEATHER_LOGS' in cmd.upper():
                print("✓ Table WEATHER_LOGS created")
            elif 'CREATE INDEX' in cmd.upper():
                success_count += 1
            elif 'CREATE VIEW' in cmd.upper() or 'CREATE OR REPLACE VIEW' in cmd.upper():
                success_count += 1
            
        except Exception as e:
            error_msg = str(e)
            # Ignore "already exists" errors
            if 'already exists' in error_msg.lower():
                continue
            else:
                print(f"⚠️  Warning on command {i}: {error_msg[:100]}")
                error_count += 1
    
    print()
    print(f"✓ {success_count} additional objects created (indexes, views)")
    
    # Verify tables exist
    print()
    print("🔍 Verifying database objects...")
    
    cursor.execute("USE DATABASE MILLIONX")
    cursor.execute("USE SCHEMA RAW_DATA")
    cursor.execute("SHOW TABLES")
    
    tables = cursor.fetchall()
    table_names = [row[1] for row in tables]
    
    expected_tables = ['SOCIAL_POSTS', 'MARKET_ORDERS', 'PRICE_HISTORY', 'WEATHER_LOGS']
    
    print()
    print("Tables found:")
    for table in expected_tables:
        if table in table_names:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} (missing)")
    
    # Get row counts
    print()
    print("Initial row counts:")
    for table in expected_tables:
        if table in table_names:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except:
                pass
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ Snowflake Schema Initialization Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Wait for OpenWeather API activation (~10 minutes)")
    print("2. Test OpenWeather API connection")
    print("3. Start Phase 2 pipeline testing")
    print()
    print("📖 Testing Guide: ../TESTING-QUICK-START.md")
    print()

if __name__ == "__main__":
    initialize_snowflake_schema()
