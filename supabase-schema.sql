-- MillionX MVP Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- MERCHANTS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS merchants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    registration_date TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================
-- ORDERS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_area VARCHAR(100),
    delivery_city VARCHAR(50),
    delivery_postal_code VARCHAR(20),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(20) DEFAULT 'COD',
    items_count INTEGER DEFAULT 1,
    is_first_order BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================
-- BLACKLIST TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    failed_deliveries INTEGER DEFAULT 1,
    total_fraud_amount DECIMAL(10,2) DEFAULT 0.00,
    last_incident_date TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT,
    added_by UUID REFERENCES merchants(id),
    severity VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================
-- RISK ASSESSMENTS TABLE (for audit trail)
-- ==============================================
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id),
    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    risk_factors JSONB,
    recommendation VARCHAR(100),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_orders_merchant_id ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_orders_risk_score ON orders(risk_score);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_blacklist_phone ON blacklist(phone);
CREATE INDEX IF NOT EXISTS idx_blacklist_severity ON blacklist(severity);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_order_id ON risk_assessments(order_id);

-- ==============================================
-- TRIGGERS FOR UPDATED_AT
-- ==============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_merchants_updated_at BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blacklist_updated_at BEFORE UPDATE ON blacklist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- SEED TEST DATA
-- ==============================================

-- Insert test merchants
INSERT INTO merchants (phone, business_name) 
VALUES 
    ('+8801712345678', 'Test Merchant Store'),
    ('+8801612345678', 'Fashion Hub BD'),
    ('+8801812345678', 'Electronics Paradise')
ON CONFLICT (phone) DO NOTHING;

-- Insert test orders
INSERT INTO orders (
    merchant_id, 
    order_id, 
    customer_phone, 
    total_amount, 
    delivery_area, 
    delivery_city,
    status,
    items_count,
    risk_score,
    risk_level,
    is_first_order
)
SELECT 
    m.id,
    'ORD-' || LPAD((ROW_NUMBER() OVER())::TEXT, 6, '0'),
    CASE 
        WHEN random() < 0.2 THEN '+8801799999999'  -- 20% blacklisted
        ELSE '+88017' || LPAD(FLOOR(random() * 100000000)::TEXT, 8, '0')
    END,
    (random() * 4000 + 200)::DECIMAL(10,2),
    CASE FLOOR(random() * 5)
        WHEN 0 THEN 'Gulshan'
        WHEN 1 THEN 'Dhanmondi'
        WHEN 2 THEN 'Mirpur'
        WHEN 3 THEN 'Uttara'
        ELSE 'Banani'
    END,
    'Dhaka',
    CASE FLOOR(random() * 4)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'delivered'
        WHEN 2 THEN 'cancelled'
        ELSE 'in_transit'
    END,
    (random() * 5 + 1)::INTEGER,
    (random() * 100)::INTEGER,
    CASE 
        WHEN random() * 100 < 40 THEN 'LOW'
        WHEN random() * 100 < 70 THEN 'MEDIUM'
        ELSE 'HIGH'
    END,
    random() < 0.3  -- 30% first orders
FROM merchants m
CROSS JOIN generate_series(1, 50)  -- 50 orders per merchant
ON CONFLICT (order_id) DO NOTHING;

-- Insert test blacklist entries
INSERT INTO blacklist (phone, failed_deliveries, total_fraud_amount, last_incident_date, reason, severity)
VALUES 
    ('+8801799999999', 3, 4500.00, NOW() - INTERVAL '2 days', 'Multiple failed deliveries - customer unreachable', 'high'),
    ('+8801788888888', 2, 2300.00, NOW() - INTERVAL '5 days', 'Refused delivery twice without reason', 'medium'),
    ('+8801777777777', 1, 800.00, NOW() - INTERVAL '1 month', 'Address not found', 'low'),
    ('+8801766666666', 4, 6200.00, NOW() - INTERVAL '3 days', 'Known fraudster - fake address', 'high'),
    ('+8801755555555', 2, 1900.00, NOW() - INTERVAL '1 week', 'COD refused at delivery', 'medium')
ON CONFLICT (phone) DO NOTHING;

-- ==============================================
-- VERIFICATION QUERIES
-- ==============================================

-- Count records in each table
SELECT 'Merchants' as table_name, COUNT(*) as count FROM merchants
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Blacklist', COUNT(*) FROM blacklist
UNION ALL
SELECT 'Risk Assessments', COUNT(*) FROM risk_assessments;

-- View sample data
SELECT 
    m.business_name,
    COUNT(o.id) as total_orders,
    AVG(o.risk_score)::DECIMAL(5,2) as avg_risk_score,
    SUM(o.total_amount) as total_revenue
FROM merchants m
LEFT JOIN orders o ON m.id = o.merchant_id
GROUP BY m.id, m.business_name
ORDER BY total_orders DESC;

-- View blacklist summary
SELECT 
    phone,
    failed_deliveries,
    total_fraud_amount,
    severity,
    last_incident_date
FROM blacklist
ORDER BY failed_deliveries DESC, total_fraud_amount DESC;
