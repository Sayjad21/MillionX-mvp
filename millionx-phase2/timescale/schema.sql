-- TimescaleDB Schema for MillionX Analytics
-- Snowflake Alternative - FREE time-series database

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Sales History Hypertable (replaces Snowflake SALES_HISTORY)
CREATE TABLE IF NOT EXISTS sales_history (
    time TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 0,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    merchant_id VARCHAR(50),
    customer_region VARCHAR(100),
    customer_city VARCHAR(100),
    payment_method VARCHAR(50),
    delivery_status VARCHAR(50),
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Convert to hypertable (time-series optimization)
SELECT create_hypertable('sales_history', 'time', if_not_exists => TRUE);

-- Social Signals Hypertable (replaces Snowflake SOCIAL_POSTS)
CREATE TABLE IF NOT EXISTS social_signals (
    time TIMESTAMPTZ NOT NULL,
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    content TEXT,
    hashtags TEXT[],
    engagement_score INTEGER DEFAULT 0,
    sentiment_score DECIMAL(3,2),
    sentiment_label VARCHAR(20),
    product_mentions TEXT[],
    author_id VARCHAR(255),
    location VARCHAR(100),
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Convert to hypertable
SELECT create_hypertable('social_signals', 'time', if_not_exists => TRUE);

-- Weather Data Hypertable
CREATE TABLE IF NOT EXISTS weather_data (
    time TIMESTAMPTZ NOT NULL,
    city VARCHAR(100) NOT NULL,
    temperature DECIMAL(5,2),
    humidity INTEGER,
    condition VARCHAR(50),
    description TEXT,
    wind_speed DECIMAL(5,2),
    precipitation DECIMAL(5,2),
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Convert to hypertable
SELECT create_hypertable('weather_data', 'time', if_not_exists => TRUE);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ts_sales_product ON sales_history (product_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ts_sales_category ON sales_history (product_category, time DESC);
CREATE INDEX IF NOT EXISTS idx_ts_sales_merchant ON sales_history (merchant_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ts_sales_region ON sales_history (customer_region, time DESC);

CREATE INDEX IF NOT EXISTS idx_ts_social_platform ON social_signals (platform, time DESC);
CREATE INDEX IF NOT EXISTS idx_ts_social_sentiment ON social_signals (sentiment_label, time DESC);

CREATE INDEX IF NOT EXISTS idx_ts_weather_city ON weather_data (city, time DESC);

-- Continuous aggregates (pre-computed rollups for faster queries)
CREATE MATERIALIZED VIEW IF NOT EXISTS sales_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    product_category,
    customer_region,
    COUNT(*) as order_count,
    SUM(quantity) as total_quantity,
    SUM(total_amount) as total_revenue,
    AVG(unit_price) as avg_price
FROM sales_history
GROUP BY day, product_category, customer_region
WITH NO DATA;

-- Refresh policy (auto-update every hour)
SELECT add_continuous_aggregate_policy('sales_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Product demand trends (7-day rolling window)
CREATE MATERIALIZED VIEW IF NOT EXISTS product_demand_trends
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    product_id,
    product_name,
    product_category,
    SUM(quantity) as daily_demand,
    AVG(unit_price) as avg_price,
    COUNT(DISTINCT merchant_id) as merchant_count
FROM sales_history
GROUP BY day, product_id, product_name, product_category
WITH NO DATA;

SELECT add_continuous_aggregate_policy('product_demand_trends',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Social sentiment trends
CREATE MATERIALIZED VIEW IF NOT EXISTS sentiment_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    platform,
    sentiment_label,
    COUNT(*) as post_count,
    AVG(engagement_score) as avg_engagement,
    AVG(sentiment_score) as avg_sentiment
FROM social_signals
WHERE sentiment_label IS NOT NULL
GROUP BY day, platform, sentiment_label
WITH NO DATA;

SELECT add_continuous_aggregate_policy('sentiment_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Retention policies (auto-delete old data)
-- Keep raw data for 90 days, aggregates for 1 year
SELECT add_retention_policy('sales_history', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('social_signals', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('weather_data', INTERVAL '90 days', if_not_exists => TRUE);

-- Compression policy (save disk space for old data)
SELECT add_compression_policy('sales_history', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('social_signals', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('weather_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE millionx_analytics TO millionx;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO millionx;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO millionx;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ TimescaleDB initialized successfully';
    RAISE NOTICE '📊 Hypertables created: sales_history, social_signals, weather_data';
    RAISE NOTICE '📈 Continuous aggregates enabled for real-time analytics';
    RAISE NOTICE '🗜️ Compression enabled (7-day delay)';
    RAISE NOTICE '♻️  Retention policy: 90 days for raw data';
END $$;
