# MillionX Quick Start Guide 🚀

## 📋 Table of Contents

1. [Run Commands](#run-commands)
2. [Using Mock Data (No Paid APIs)](#using-mock-data-no-paid-apis)
3. [Complete Pipeline Explanation](#complete-pipeline-explanation)

---

## 🎯 Run Commands

### Phase 1: COD Shield (WhatsApp Bot + Risk Engine)

```powershell
# Navigate to project root
cd g:\MillionX-mvp

# Start all Phase 1 services (Redis, FastAPI, WhatsApp Bot)
docker-compose up -d

# Check if services are running
docker ps

# View logs
docker-compose logs -f

# Access services:
# - FastAPI Risk Engine: http://localhost:8000/docs
# - WhatsApp Bot: http://localhost:3000
# - Redis: localhost:6379

# Stop services
docker-compose down
```

### Phase 2: Data Pipeline (Kafka, Scrapers, Stream Processing)

```powershell
# Navigate to Phase 2 directory
cd g:\MillionX-mvp\millionx-phase2

# Start Kafka infrastructure
docker-compose -f docker-compose.kafka.yml up -d

# Wait 30 seconds for Kafka to start
Start-Sleep -Seconds 30

# Create Kafka topics
bash kafka-topics.sh
# Or on Windows PowerShell:
docker exec millionx-kafka kafka-topics --create --topic source.social.tiktok --bootstrap-server localhost:9092 --partitions 6 --replication-factor 1

# Check services:
# - Kafka UI: http://localhost:8080
# - Grafana: http://localhost:3001 (admin/admin123)
# - Prometheus: http://localhost:9090
# - Weaviate: http://localhost:8082

# Stop services
docker-compose -f docker-compose.kafka.yml down
```

---

## 🎭 Using Mock Data (No Paid APIs)

### Paid APIs Required in Phase 2:

1. **TikTok/Facebook Scraping** → Requires proxies ($500/month)
2. **OpenWeatherMap** → FREE tier available (1000 calls/day)
3. **Snowflake** → FREE 30-day trial
4. **Shopify/Daraz** → Requires merchant accounts

### Solution: Mock Data Generator

I'll create a mock data generator that bypasses all paid APIs:

```powershell
# Navigate to Phase 2
cd g:\MillionX-mvp\millionx-phase2

# Run mock data generator (sends data to Kafka)
python mock_data_generator.py

# This will:
# 1. Generate fake social media posts
# 2. Generate fake e-commerce orders
# 3. Add mock weather data
# 4. Send everything through the pipeline
```

---

## 📊 Complete Pipeline Explanation (Simple)

### Phase 1: COD Shield (Fraud Detection)

```
User sends WhatsApp message
        ↓
WhatsApp Bot receives message
        ↓
Extracts phone number from message
        ↓
Calls FastAPI Risk Engine
        ↓
Risk Engine checks:
  - Redis blacklist (is phone blocked?)
  - Order history (first-time buyer?)
  - Risk score calculated (0-100)
        ↓
Returns risk level: LOW / MEDIUM / HIGH
        ↓
WhatsApp Bot sends response to user
```

**Example:**

```
Merchant: "risk check +8801712345678"
Bot: "✅ LOW RISK (score: 25/100) - Safe to ship COD"
```

---

### Phase 2: Data Pipeline (The Complete Flow)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
├─────────────────┬──────────────┬─────────────────────────────┤
│ Social Media    │ E-Commerce   │ Weather                     │
│ (TikTok/FB)     │ (Shopify)    │ (OpenWeather)               │
└────────┬────────┴──────┬───────┴──────┬──────────────────────┘
         │                │              │
         │ STEP 1: SCRAPE DATA           │
         ▼                ▼              ▼
┌────────────────────────────────────────────────────────────┐
│                    KAFKA TOPICS                             │
│  source.social.tiktok                                       │
│  source.market.shopify                                      │
│  context.weather                                            │
└───────────────────────┬────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         │ STEP 2: PROCESS DATA        │
         ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Privacy      │ │ Context     │ │ Embedding    │
│ Shield       │ │ Enricher    │ │ Service      │
│              │ │             │ │              │
│ Hashes PII   │ │ Adds weather│ │ Creates AI   │
│ (phone/email)│ │ + category  │ │ vectors      │
└──────┬───────┘ └──────┬──────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
         STEP 3: STORE DATA
                        ▼
┌─────────────────────────────────────────────────┐
│              STORAGE LAYER                       │
├────────────────────┬─────────────────────────────┤
│   Snowflake        │    Weaviate                 │
│   (Analytics)      │    (Vector Search)          │
│                    │                             │
│ • Social posts     │ • Embeddings for search     │
│ • Orders           │ • Product recommendations   │
│ • Price history    │ • Similar content           │
└────────────────────┴─────────────────────────────┘
```

---

### Detailed Step-by-Step:

#### **STEP 1: Data Collection** (Week 2)

- **TikTok Scraper**: Searches for keywords like "phone", "laptop"
  - Extracts: post content, likes, comments, shares
  - Uses proxies to avoid being blocked
- **Shopify Integration**: Connects to your store
  - Pulls: orders, customer info, products
- **Weather Fetcher**: Gets weather for 8 Bangladesh cities
  - Every hour via cron job
  - FREE OpenWeatherMap API

**Output**: Raw JSON data → Kafka topics

---

#### **STEP 2: Data Processing** (Week 3)

##### A. Privacy Shield (PII Anonymization)

```
INPUT: "Call me at +8801712345678 or john@email.com"

PROCESSING:
- Detects phone number pattern
- Detects email pattern
- Hashes with SHA-256

OUTPUT: "Call me at PHONE_f7e2c9a4 or EMAIL_a3f5b9c2"
```

##### B. Context Enricher

```
INPUT: Post about "new smartphone for sale"

PROCESSING:
- Detects product category: "smartphone"
- Fetches weather: "Clear, 28°C, 65% humidity"
- Adds timestamp info: "Weekend, 2 PM"

OUTPUT: Same post + metadata (category, weather, time context)
```

##### C. Embedding Service

```
INPUT: "Amazing iPhone 15 Pro for sale in Dhaka"

PROCESSING:
- Uses AI model (Sentence Transformers)
- Converts text to 384-dimensional vector
- Example: [0.23, -0.45, 0.89, ..., 0.12]

OUTPUT: Vector that captures meaning
```

**Why?** Similar products have similar vectors, enabling AI search.

---

#### **STEP 3: Data Storage** (Week 4)

##### A. Snowflake (Analytics Database)

```sql
-- Stores structured data for reports

SELECT
  product_category,
  COUNT(*) as order_count,
  AVG(total_price) as avg_price
FROM market_orders
WHERE order_date > '2025-12-01'
GROUP BY product_category;
```

**Tables:**

- `social_posts` - TikTok/Facebook data
- `market_orders` - Shopify/Daraz orders
- `price_history` - Price changes over time
- `weather_logs` - Weather data

##### B. Weaviate (Vector Database)

```python
# Semantic search: Find similar products

query = "cheap smartphone under 20000 taka"
results = weaviate.search(query, limit=10)

# Returns: Products with similar meaning,
# not just keyword matches
```

---

## 🎭 Mock Data Flow (For Testing Without APIs)

```
mock_data_generator.py
        ↓
Generates fake data:
  - 100 social posts (TikTok/FB style)
  - 50 orders (Shopify style)
  - Weather data for Dhaka
        ↓
Sends to Kafka topics
        ↓
Stream processors run (Privacy, Context, Embedding)
        ↓
Data stored in Snowflake + Weaviate
        ↓
You can query and see results!
```

---

## 🔍 What Each Component Does (ELI5)

| Component             | What It Does                            | Why It Matters                                             |
| --------------------- | --------------------------------------- | ---------------------------------------------------------- |
| **Kafka**             | Message highway (like a postal service) | Connects all parts, handles millions of messages           |
| **Privacy Shield**    | Hides sensitive info (phone/email)      | Protects customer privacy, GDPR compliance                 |
| **Context Enricher**  | Adds weather + product category         | Helps AI understand: "phones sell more on sunny days"      |
| **Embedding Service** | Converts text to numbers                | Enables AI search: "cheap phone" finds "affordable mobile" |
| **Snowflake**         | Big data warehouse                      | Fast analytics: "How many orders today?"                   |
| **Weaviate**          | Smart search engine                     | "Show me products like this iPhone"                        |

---

## 🎓 Learn the Codebase Fast

### Critical Files to Read (in order):

1. **Phase 1 (Simple)**

   - [fastapi-risk-engine/main.py](fastapi-risk-engine/main.py) - Risk scoring logic (279 lines)
   - [whatsapp-bot/index.js](whatsapp-bot/index.js) - WhatsApp message handling

2. **Phase 2 (Advanced)**
   - [millionx-phase2/scrapers/shared/models.py](millionx-phase2/scrapers/shared/models.py) - Data structures
   - [millionx-phase2/stream-processors/privacy_shield.py](millionx-phase2/stream-processors/privacy_shield.py) - PII removal
   - [millionx-phase2/snowflake/schema-setup.sql](millionx-phase2/snowflake/schema-setup.sql) - Database design

### Code Structure:

```
millionx-mvp/
├── Phase 1: COD Shield (SIMPLE)
│   ├── fastapi-risk-engine/     ← Fraud detection API
│   └── whatsapp-bot/            ← Chat interface
│
└── millionx-phase2/             ← Data Pipeline (COMPLEX)
    ├── scrapers/                ← Collect data
    │   ├── social/              ← TikTok, Facebook
    │   └── market/              ← Shopify, Daraz
    │
    ├── stream-processors/       ← Process data
    │   ├── privacy_shield.py    ← Remove PII
    │   ├── context_enricher.py  ← Add metadata
    │   └── embedding_service.py ← AI vectors
    │
    ├── snowflake/               ← Analytics storage
    └── weaviate/                ← Vector search
```

---

## 🎯 Next Steps

1. **Start with Phase 1** (Easy)

   ```powershell
   cd g:\MillionX-mvp
   docker-compose up -d
   # Visit http://localhost:8000/docs
   ```

2. **Test with Mock Data** (No APIs needed)

   ```powershell
   cd millionx-phase2
   python mock_data_generator.py
   ```

3. **Explore Kafka UI**

   - Visit http://localhost:8080
   - Watch messages flow through topics

4. **Query Results**
   - Snowflake: See processed data
   - Weaviate: Test AI search

---

## 📞 Quick Help

**Issue**: Docker containers not starting  
**Fix**: `docker-compose down -v && docker-compose up -d`

**Issue**: Port already in use  
**Fix**: Change port in `docker-compose.yml`

**Issue**: Kafka not receiving messages  
**Fix**: Check topics exist: `docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092`

---

**Ready?** Run the mock data generator next! 🚀
