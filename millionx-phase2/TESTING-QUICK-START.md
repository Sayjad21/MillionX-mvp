# Phase 2 Testing Quick Start Guide

## 🎯 Goal
Get Phase 2 pipeline running end-to-end with minimal setup (no real scraping yet).

**Time Required:** 30 minutes  
**Required Credentials:** Snowflake + OpenWeather API (both free)

---

## Step 1: Get Required Credentials (15 mins)

### A. Snowflake Account
```bash
1. Go to https://signup.snowflake.com
2. Choose "Standard" edition (30-day trial)
3. Select region (closest to Bangladesh: ap-southeast-1 or us-east-1)
4. Complete signup
5. Note your credentials:
   - Account URL: <account>.<region>.snowflakecomputing.com
   - Username: <your_email>
   - Password: <your_password>
```

### B. OpenWeatherMap API Key
```bash
1. Go to https://openweathermap.org/api
2. Sign up for free account
3. Go to "API Keys" tab
4. Copy your API key
5. Wait 10 minutes for activation (important!)
```

---

## Step 2: Configure Environment (5 mins)

### Create .env file
```bash
cd millionx-phase2

# Create .env file with your credentials
cat > .env << EOF
# Snowflake
SNOWFLAKE_ACCOUNT=<your_account>.<region>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<password>
SNOWFLAKE_DATABASE=MILLIONX
SNOWFLAKE_SCHEMA=RAW_DATA
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# Weather API
OPENWEATHER_API_KEY=<your_api_key>

# Kafka (already running from Week 1)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Privacy Salt (change in production!)
PRIVACY_SALT=testing_salt_2025

# Redis (for context enricher)
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
```

---

## Step 3: Initialize Snowflake Schema (3 mins)

```bash
cd millionx-phase2/snowflake

# Option 1: Using Snowflake Web UI (easier)
1. Login to https://<account>.<region>.snowflakecomputing.com
2. Click "Worksheets" in left menu
3. Click "+" to create new worksheet
4. Copy-paste contents of schema-setup.sql
5. Click "Run All" button (top right)
6. Wait for ~2 minutes (creates database, tables, indexes, views)

# Option 2: Using snowsql CLI (if installed)
snowsql -a <account> -u <username> -f schema-setup.sql

# Expected output:
# ✓ Database MILLIONX created
# ✓ Schema RAW_DATA created
# ✓ 4 tables created (SOCIAL_POSTS, MARKET_ORDERS, PRICE_HISTORY, WEATHER_LOGS)
# ✓ 15 indexes created
# ✓ 8 views created
```

---

## Step 4: Start All Services (5 mins)

### A. Verify Week 1 Infrastructure is Running
```bash
cd millionx-phase2

# Check all services
docker ps

# Should see 7 running containers:
# - millionx-kafka
# - millionx-zookeeper
# - millionx-kafka-ui (http://localhost:8080)
# - millionx-kafka-connect
# - millionx-prometheus
# - millionx-grafana (http://localhost:3001)
# - millionx-weaviate

# If not running, start them:
docker-compose -f docker-compose.kafka.yml up -d
```

### B. Initialize Weaviate Schema
```bash
cd millionx-phase2/weaviate

# Install dependencies (if not already)
pip install -r requirements.txt

# Create vector schema
python schema-setup.py

# Expected output:
# ✓ Created SocialPost collection
# ✓ Created MarketOrder collection
# ✓ Schema setup completed successfully!
```

### C. Start Stream Processors
```bash
cd millionx-phase2/stream-processors

# Install dependencies (if not already)
pip install -r requirements.txt

# Start all 4 processors in background
faust -A privacy_shield worker -l info > logs/privacy_shield.log 2>&1 &
faust -A context_enricher worker -l info > logs/context_enricher.log 2>&1 &
faust -A embedding_service worker -l info > logs/embedding_service.log 2>&1 &
faust -A schema_validator worker -l info > logs/schema_validator.log 2>&1 &

# Verify all started
ps aux | grep faust

# Should see 4 faust processes running
```

### D. Start Snowflake Batch Loader
```bash
cd millionx-phase2/snowflake

# Install dependencies (if not already)
pip install -r requirements.txt

# Start batch loader (consumes from Kafka, loads to Snowflake)
python snowflake_batch_sink.py > logs/snowflake_sink.log 2>&1 &

# Check it's running
tail -f logs/snowflake_sink.log
# Should see: "Connected to Snowflake: MILLIONX.RAW_DATA"
```

---

## Step 5: Run End-to-End Test (2 mins)

### A. Send Test Data to Kafka
```bash
cd millionx-phase2

# Create test script
cat > test_pipeline.py << 'EOF'
from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Test social post
social_post = {
    "post_id": "test_001",
    "platform": "tiktok",
    "content": "Testing MillionX pipeline! Contact me at john.doe@email.com or +8801712345678",
    "author_handle": "@testuser",
    "engagement_count": 1000,
    "timestamp": datetime.now().isoformat(),
    "hashtags": ["test", "millionx"],
    "location": "Dhaka"
}

# Test market order
market_order = {
    "order_id": "test_order_001",
    "merchant_id": "merchant_001",
    "product_id": "product_001",
    "product_name": "Test Product",
    "quantity": 5,
    "unit_price": 1500.00,
    "total_amount": 7500.00,
    "customer_location": "Dhaka",
    "timestamp": datetime.now().isoformat()
}

print("Sending test social post...")
producer.send('source.social.tiktok', social_post)
print("✓ Sent to source.social.tiktok")

print("Sending test market order...")
producer.send('source.market.shopify', market_order)
print("✓ Sent to source.market.shopify")

producer.flush()
print("\n✅ Test data sent successfully!")
print("\nNext steps:")
print("1. Check stream processor logs (they should process these messages)")
print("2. Wait 60 seconds for Snowflake batch flush")
print("3. Query Snowflake to verify data landed")
EOF

python test_pipeline.py
```

### B. Verify Data Flow

**1. Check Kafka UI:**
```bash
# Open in browser
http://localhost:8080

# Navigate to Topics:
# - source.social.tiktok → Should see 1 message
# - source.market.shopify → Should see 1 message
# - sink.weaviate.vectors → Should see processed messages
```

**2. Check Stream Processor Logs:**
```bash
# Check privacy shield (should anonymize PII)
tail -n 20 stream-processors/logs/privacy_shield.log

# Should see:
# "Anonymized email: john.doe@email.com → EMAIL_a3f5b9c2"
# "Anonymized phone: +8801712345678 → PHONE_7f8d3e9c"
```

**3. Check Snowflake (after 60 seconds):**
```sql
-- Login to Snowflake web UI
-- Go to Worksheets
-- Run these queries:

-- Check if data arrived
SELECT COUNT(*) FROM MILLIONX.RAW_DATA.SOCIAL_POSTS;
-- Expected: 1 row

SELECT COUNT(*) FROM MILLIONX.RAW_DATA.MARKET_ORDERS;
-- Expected: 1 row

-- Verify PII was anonymized
SELECT content FROM MILLIONX.RAW_DATA.SOCIAL_POSTS;
-- Should see hashed email/phone, not original values

-- Check metadata
SELECT 
    post_id,
    platform,
    _anonymized,
    ingestion_time
FROM MILLIONX.RAW_DATA.SOCIAL_POSTS;
```

**4. Check Weaviate:**
```bash
# Query vector count
curl http://localhost:8082/v1/objects | jq '.totalResults'
# Expected: 2 objects (1 social post, 1 market order)

# Semantic search test
curl -X POST http://localhost:8082/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ Get { SocialPost(nearText: {concepts: [\"testing\"]}) { content platform }}}"
  }' | jq
# Should return the test post
```

**5. Check Weather Data:**
```bash
# Manually trigger weather fetch
cd millionx-phase2/weather-fetcher
python weather_fetcher.py

# Expected output:
# ✓ Fetched weather for Dhaka: Clear, 28.5°C
# ✓ Published to Kafka: context.weather

# Verify in Snowflake (should auto-flow)
SELECT COUNT(*) FROM MILLIONX.RAW_DATA.WEATHER_LOGS;
# Expected: 8 rows (8 Bangladesh cities)
```

---

## Step 6: Monitor with Grafana (2 mins)

```bash
1. Open Grafana: http://localhost:3001
2. Login: admin / admin123
3. Go to Dashboards → Browse
4. Open "MillionX Phase 2 - Overview"
5. Verify metrics:
   - Kafka Topics Message Count > 0
   - Stream Processor Throughput > 0
   - Snowflake Ingestion Rate > 0
   - Weaviate Object Count > 0
```

---

## ✅ Success Criteria

If all these pass, Phase 2 is working:

- [x] Kafka accepting messages (visible in Kafka UI)
- [x] Stream processors consuming and transforming data (check logs)
- [x] PII anonymized (verify in Snowflake)
- [x] Data landing in Snowflake (query returns rows)
- [x] Vectors stored in Weaviate (curl returns objects)
- [x] Weather data flowing (8 cities in WEATHER_LOGS table)
- [x] Grafana dashboards showing metrics

---

## 🚨 Troubleshooting

### Issue: "Snowflake authentication failed"
```bash
# Verify credentials
echo $SNOWFLAKE_ACCOUNT
echo $SNOWFLAKE_USER

# Test connection
python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    account='$SNOWFLAKE_ACCOUNT',
    user='$SNOWFLAKE_USER',
    password='$SNOWFLAKE_PASSWORD'
)
print('✓ Connected to Snowflake')
"
```

### Issue: "OpenWeather API returns 401"
```bash
# Check if API key is activated (needs 10 min after signup)
curl "https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid=$OPENWEATHER_API_KEY"

# If error, wait 10 more minutes and retry
```

### Issue: "Stream processors not consuming"
```bash
# Check if they're subscribed to topics
faust -A privacy_shield inspect

# Restart all processors
pkill -f faust
cd millionx-phase2/stream-processors
./start_all.sh  # Or manually restart each
```

### Issue: "Data not appearing in Snowflake"
```bash
# Check batch loader logs
tail -f millionx-phase2/snowflake/logs/snowflake_sink.log

# Check batch buffer (might need to wait 60 seconds)
# Or reduce FLUSH_INTERVAL_SECONDS in .env to 10 seconds for testing

# Manual flush test
python -c "
from snowflake_batch_sink import SnowflakeBatchSink
sink = SnowflakeBatchSink(batch_size=1)  # Flush immediately
# Run for 30 seconds
"
```

---

## 📊 Next Steps After Testing

Once end-to-end test passes:

1. **Phase 2 Complete** ✅
2. **Optional: Add Real Scrapers**
   - Setup proxy credentials (BrightData/Smartproxy)
   - Add social media API tokens
   - Deploy K8s CronJobs for automated scraping

3. **Move to Phase 3: AI Models**
   - NeuralProphet demand forecasting
   - LangGraph agent orchestration
   - Real-time analytics dashboard

---

## 📞 Quick Reference

**Kafka UI:** http://localhost:8080  
**Grafana:** http://localhost:3001 (admin/admin123)  
**Prometheus:** http://localhost:9090  
**Weaviate:** http://localhost:8082  

**Logs Location:** `millionx-phase2/stream-processors/logs/`  
**Config:** `millionx-phase2/.env`  

**Stop All Services:**
```bash
# Stop stream processors
pkill -f faust

# Stop batch loader
pkill -f snowflake_batch_sink

# Stop Docker services
docker-compose -f docker-compose.kafka.yml down
```

**Restart All Services:**
```bash
# Start Docker services
docker-compose -f docker-compose.kafka.yml up -d

# Start stream processors
cd millionx-phase2/stream-processors && ./start_all.sh

# Start batch loader
cd millionx-phase2/snowflake && python snowflake_batch_sink.py &
```

---

**Last Updated:** December 20, 2025  
**Status:** Ready for testing  
**Prerequisites:** Snowflake account + OpenWeather API key
