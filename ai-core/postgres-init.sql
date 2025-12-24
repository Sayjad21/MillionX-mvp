-- PostgreSQL Initialization Script for MillionX AI Core
-- Creates tables for sales history and social signals

-- Sales History Table
CREATE TABLE IF NOT EXISTS sales_history (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 0,
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    customer_region VARCHAR(100),
    merchant_id VARCHAR(50),
    payment_method VARCHAR(50),
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Social Signals Table
CREATE TABLE IF NOT EXISTS social_signals (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    hashtags TEXT[],
    engagement_score INTEGER DEFAULT 0,
    sentiment_score DECIMAL(3,2),
    product_mentions TEXT[],
    author VARCHAR(255),
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales_history(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales_history(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_history(product_category);
CREATE INDEX IF NOT EXISTS idx_sales_merchant ON sales_history(merchant_id);

CREATE INDEX IF NOT EXISTS idx_social_platform ON social_signals(platform);
CREATE INDEX IF NOT EXISTS idx_social_posted_at ON social_signals(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_social_post_id ON social_signals(post_id);

-- Create function to update ingested_at timestamp
CREATE OR REPLACE FUNCTION update_ingested_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ingested_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE millionx TO millionx;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO millionx;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO millionx;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ MillionX PostgreSQL database initialized successfully';
END $$;
