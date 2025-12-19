-- MillionX Snowflake Schema Setup
-- Phase 2 Week 4: Data Warehouse Configuration

-- =====================================
-- 1. DATABASE AND SCHEMA SETUP
-- =====================================

-- Create database
CREATE DATABASE IF NOT EXISTS MILLIONX;

-- Use database
USE DATABASE MILLIONX;

-- Create schema for raw data
CREATE SCHEMA IF NOT EXISTS RAW_DATA;

-- Use schema
USE SCHEMA RAW_DATA;

-- =====================================
-- 2. SOCIAL POSTS TABLE
-- =====================================

CREATE TABLE IF NOT EXISTS SOCIAL_POSTS (
    -- Primary identifiers
    post_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    
    -- Content fields (anonymized)
    content TEXT,
    author VARCHAR(255),  -- Hashed by Privacy Shield
    
    -- Engagement metrics
    engagement_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    
    -- Metadata
    post_url VARCHAR(500),
    hashtags ARRAY,
    location VARCHAR(255),
    
    -- Timestamps
    posted_at TIMESTAMP_NTZ,
    
    -- Enrichment context (from Context Enricher)
    product_category VARCHAR(100),
    category_confidence FLOAT,
    weather_data VARIANT,
    temporal_context VARIANT,
    
    -- Vector embedding (from Embedding Service)
    embedding ARRAY,  -- 384-dimensional vector
    embedding_model VARCHAR(100),
    
    -- Processing metadata
    anonymized BOOLEAN DEFAULT FALSE,
    enriched BOOLEAN DEFAULT FALSE,
    anonymization_version VARCHAR(20),
    enrichment_timestamp TIMESTAMP_NTZ,
    embedding_timestamp TIMESTAMP_NTZ,
    
    -- Kafka metadata (added by Snowflake Connector)
    kafka_topic VARCHAR(255),
    kafka_partition INTEGER,
    kafka_offset BIGINT,
    kafka_timestamp TIMESTAMP_NTZ,
    
    -- Ingestion tracking
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_social_platform ON SOCIAL_POSTS(platform);
CREATE INDEX IF NOT EXISTS idx_social_posted_at ON SOCIAL_POSTS(posted_at);
CREATE INDEX IF NOT EXISTS idx_social_product_category ON SOCIAL_POSTS(product_category);
CREATE INDEX IF NOT EXISTS idx_social_engagement ON SOCIAL_POSTS(engagement_count);
CREATE INDEX IF NOT EXISTS idx_social_ingestion_time ON SOCIAL_POSTS(ingestion_time);

-- =====================================
-- 3. MARKET ORDERS TABLE
-- =====================================

CREATE TABLE IF NOT EXISTS MARKET_ORDERS (
    -- Primary identifiers
    order_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    
    -- Customer data (anonymized)
    customer_id VARCHAR(255),  -- Hashed by Privacy Shield
    email VARCHAR(255),  -- Hashed
    
    -- Product information
    product_id VARCHAR(255),
    product_name VARCHAR(500),
    category VARCHAR(100),
    
    -- Pricing
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'BDT',
    
    -- Order status
    status VARCHAR(50),
    payment_method VARCHAR(100),
    payment_status VARCHAR(50),
    
    -- Shipping information
    shipping_region VARCHAR(255),
    shipping_city VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP_NTZ,
    updated_at TIMESTAMP_NTZ,
    
    -- Enrichment context
    product_category VARCHAR(100),
    category_confidence FLOAT,
    weather_data VARIANT,
    temporal_context VARIANT,
    
    -- Vector embedding
    embedding ARRAY,  -- 384-dimensional vector
    embedding_model VARCHAR(100),
    
    -- Processing metadata
    anonymized BOOLEAN DEFAULT FALSE,
    enriched BOOLEAN DEFAULT FALSE,
    anonymization_version VARCHAR(20),
    enrichment_timestamp TIMESTAMP_NTZ,
    embedding_timestamp TIMESTAMP_NTZ,
    
    -- Kafka metadata
    kafka_topic VARCHAR(255),
    kafka_partition INTEGER,
    kafka_offset BIGINT,
    kafka_timestamp TIMESTAMP_NTZ,
    
    -- Ingestion tracking
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_market_platform ON MARKET_ORDERS(platform);
CREATE INDEX IF NOT EXISTS idx_market_customer ON MARKET_ORDERS(customer_id);
CREATE INDEX IF NOT EXISTS idx_market_product ON MARKET_ORDERS(product_id);
CREATE INDEX IF NOT EXISTS idx_market_status ON MARKET_ORDERS(status);
CREATE INDEX IF NOT EXISTS idx_market_created_at ON MARKET_ORDERS(created_at);
CREATE INDEX IF NOT EXISTS idx_market_product_category ON MARKET_ORDERS(product_category);
CREATE INDEX IF NOT EXISTS idx_market_ingestion_time ON MARKET_ORDERS(ingestion_time);

-- =====================================
-- 4. PRICE HISTORY TABLE (Analytics)
-- =====================================

CREATE TABLE IF NOT EXISTS PRICE_HISTORY (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(500),
    platform VARCHAR(50),
    unit_price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'BDT',
    recorded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Track price changes
    price_change_percent FLOAT,
    previous_price DECIMAL(10, 2)
);

CREATE INDEX IF NOT EXISTS idx_price_product ON PRICE_HISTORY(product_id);
CREATE INDEX IF NOT EXISTS idx_price_recorded_at ON PRICE_HISTORY(recorded_at);

-- =====================================
-- 5. WEATHER LOGS TABLE (Context)
-- =====================================

CREATE TABLE IF NOT EXISTS WEATHER_LOGS (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'Bangladesh',
    temperature FLOAT,
    humidity INTEGER,
    conditions VARCHAR(100),
    description VARCHAR(255),
    wind_speed FLOAT,
    is_extreme_weather BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE INDEX IF NOT EXISTS idx_weather_city ON WEATHER_LOGS(city);
CREATE INDEX IF NOT EXISTS idx_weather_recorded_at ON WEATHER_LOGS(recorded_at);
CREATE INDEX IF NOT EXISTS idx_weather_extreme ON WEATHER_LOGS(is_extreme_weather);

-- =====================================
-- 6. VIEWS FOR ANALYTICS
-- =====================================

-- Recent social engagement trends
CREATE OR REPLACE VIEW VW_RECENT_SOCIAL_TRENDS AS
SELECT 
    platform,
    product_category,
    COUNT(*) as post_count,
    AVG(engagement_count) as avg_engagement,
    MAX(engagement_count) as max_engagement,
    DATE_TRUNC('hour', posted_at) as hour
FROM SOCIAL_POSTS
WHERE posted_at > DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY platform, product_category, DATE_TRUNC('hour', posted_at)
ORDER BY hour DESC, avg_engagement DESC;

-- Product demand by region
CREATE OR REPLACE VIEW VW_PRODUCT_DEMAND_BY_REGION AS
SELECT 
    product_category,
    shipping_region,
    COUNT(*) as order_count,
    SUM(quantity) as total_quantity,
    SUM(total_price) as total_revenue,
    AVG(total_price) as avg_order_value,
    DATE_TRUNC('day', created_at) as day
FROM MARKET_ORDERS
WHERE created_at > DATEADD(day, -30, CURRENT_TIMESTAMP())
  AND status IN ('confirmed', 'shipped', 'delivered')
GROUP BY product_category, shipping_region, DATE_TRUNC('day', created_at)
ORDER BY day DESC, total_revenue DESC;

-- Weather impact on orders
CREATE OR REPLACE VIEW VW_WEATHER_ORDER_CORRELATION AS
SELECT 
    w.city,
    w.conditions,
    w.is_extreme_weather,
    COUNT(o.order_id) as order_count,
    AVG(o.total_price) as avg_order_value,
    DATE_TRUNC('hour', w.recorded_at) as hour
FROM WEATHER_LOGS w
LEFT JOIN MARKET_ORDERS o 
    ON w.city = o.shipping_city 
    AND DATE_TRUNC('hour', w.recorded_at) = DATE_TRUNC('hour', o.created_at)
WHERE w.recorded_at > DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY w.city, w.conditions, w.is_extreme_weather, DATE_TRUNC('hour', w.recorded_at)
ORDER BY hour DESC;

-- =====================================
-- 7. COST MONITORING QUERIES
-- =====================================

-- Daily ingestion volume
CREATE OR REPLACE VIEW VW_DAILY_INGESTION_STATS AS
SELECT 
    DATE_TRUNC('day', ingestion_time) as day,
    'social_posts' as table_name,
    COUNT(*) as record_count
FROM SOCIAL_POSTS
WHERE ingestion_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY DATE_TRUNC('day', ingestion_time)
UNION ALL
SELECT 
    DATE_TRUNC('day', ingestion_time) as day,
    'market_orders' as table_name,
    COUNT(*) as record_count
FROM MARKET_ORDERS
WHERE ingestion_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY DATE_TRUNC('day', ingestion_time)
ORDER BY day DESC, table_name;

-- Warehouse credit usage (for cost tracking)
CREATE OR REPLACE VIEW VW_WAREHOUSE_COST_TRACKING AS
SELECT 
    start_time,
    end_time,
    warehouse_name,
    credits_used,
    credits_used * 2.5 as estimated_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time > DATEADD(day, -30, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- =====================================
-- 8. DATA QUALITY CHECKS
-- =====================================

-- Check for null embeddings (should investigate if count > 0)
CREATE OR REPLACE VIEW VW_DATA_QUALITY_EMBEDDINGS AS
SELECT 
    'social_posts' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as missing_embeddings,
    SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as missing_percent
FROM SOCIAL_POSTS
WHERE ingestion_time > DATEADD(day, -1, CURRENT_TIMESTAMP())
UNION ALL
SELECT 
    'market_orders' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as missing_embeddings,
    SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as missing_percent
FROM MARKET_ORDERS
WHERE ingestion_time > DATEADD(day, -1, CURRENT_TIMESTAMP());

-- Check anonymization coverage
CREATE OR REPLACE VIEW VW_DATA_QUALITY_ANONYMIZATION AS
SELECT 
    'social_posts' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN anonymized = TRUE THEN 1 ELSE 0 END) as anonymized_records,
    SUM(CASE WHEN anonymized = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as anonymized_percent
FROM SOCIAL_POSTS
WHERE ingestion_time > DATEADD(day, -1, CURRENT_TIMESTAMP())
UNION ALL
SELECT 
    'market_orders' as table_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN anonymized = TRUE THEN 1 ELSE 0 END) as anonymized_records,
    SUM(CASE WHEN anonymized = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as anonymized_percent
FROM MARKET_ORDERS
WHERE ingestion_time > DATEADD(day, -1, CURRENT_TIMESTAMP());

-- =====================================
-- SETUP COMPLETE
-- =====================================

SELECT 'Snowflake schema setup complete!' as status;
SELECT 'Tables created: SOCIAL_POSTS, MARKET_ORDERS, PRICE_HISTORY, WEATHER_LOGS' as info;
SELECT 'Views created: 6 analytical views + 2 data quality views' as info;
