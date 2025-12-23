# MillionX Pipeline Flow - Visual Guide

## 🎯 The Complete Journey of Data

This document shows exactly what happens to your data from collection to storage.

---

## Phase 1: COD Shield (Fraud Detection)

### Simple 5-Step Flow:

```
STEP 1: User Action
┌─────────────────────────────────┐
│ Merchant sends WhatsApp message │
│ "risk check +8801712345678"     │
└────────────┬────────────────────┘
             │
             ▼
STEP 2: Bot Receives
┌─────────────────────────────────┐
│ WhatsApp Bot (Node.js)          │
│ - Parses message                │
│ - Extracts phone number         │
└────────────┬────────────────────┘
             │
             ▼
STEP 3: Risk Check
┌─────────────────────────────────┐
│ FastAPI Risk Engine             │
│ - Checks Redis blacklist        │
│ - Calculates risk score (0-100) │
│ - Factors: blacklist, history   │
└────────────┬────────────────────┘
             │
             ▼
STEP 4: Score Analysis
┌─────────────────────────────────┐
│ Risk Level Determination        │
│ 0-40:  LOW RISK ✅              │
│ 41-70: MEDIUM RISK ⚠️           │
│ 71+:   HIGH RISK ❌             │
└────────────┬────────────────────┘
             │
             ▼
STEP 5: Response
┌─────────────────────────────────┐
│ WhatsApp Bot Replies            │
│ "✅ LOW RISK (score: 25/100)"   │
│ "Safe to ship COD"              │
└─────────────────────────────────┘
```

### Real Example:

```
INPUT:  "risk check +8801712345678"

PROCESS:
1. Phone extracted: +8801712345678
2. Redis check: Not in blacklist ✓
3. Order history: 0 previous orders (first-time buyer)
4. Calculate score: 30 points (first-time = +30)
5. Risk level: LOW (30 < 40)

OUTPUT: "✅ LOW RISK (score: 30/100)
         Factors:
         - Not blacklisted ✓
         - First-time buyer ⚠️
         Recommendation: Safe to proceed with COD"
```

---

## Phase 2: Data Pipeline (The Complete System)

### Overview - 10,000 Foot View:

```
COLLECT DATA → PROCESS DATA → STORE DATA → USE DATA
(Scrapers)     (Stream Proc)  (Databases)  (Analytics)
```

---

### Detailed Flow - What Happens to One Social Media Post:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MINUTE 0: DATA COLLECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TikTok Post Found:
┌──────────────────────────────────────────────────┐
│ "Amazing iPhone 15 for sale! 🔥                  │
│  Only 120,000 Taka!                              │
│  Call me: +8801712345678                         │
│  Email: john.doe@email.com"                      │
│                                                  │
│ 👍 Likes: 1,500                                  │
│ 💬 Comments: 250                                 │
│ 🔄 Shares: 50                                    │
│ 📍 Location: Dhaka                               │
└──────────────────────────────────────────────────┘

↓ TikTok Scraper runs (every hour via CronJob)
↓ Extracts all data using Playwright

Raw JSON Created:
{
  "post_id": "tiktok_98765",
  "content": "Amazing iPhone 15 for sale! Call me: +8801712345678...",
  "likes_count": 1500,
  "location": "Dhaka",
  "timestamp": "2025-12-23T10:30:00Z"
}

↓ Sent to Kafka

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MINUTE 0-1: KAFKA INGESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Message arrives at:
┌──────────────────────────────────────┐
│ KAFKA TOPIC: source.social.tiktok    │
│ Partition: 3                         │
│ Offset: 12,567                       │
└──────────────────────────────────────┘

↓ 3 stream processors listening...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MINUTE 1-2: STREAM PROCESSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROCESSOR 1: Privacy Shield
┌──────────────────────────────────────────────────┐
│ 🔒 DETECTING PII...                              │
│                                                  │
│ Found: +8801712345678 (phone)                    │
│   → Hashing with SHA-256                         │
│   → Result: PHONE_f7e2c9a4b3d5e8f1               │
│                                                  │
│ Found: john.doe@email.com (email)                │
│   → Hashing with SHA-256                         │
│   → Result: EMAIL_a3f5b9c2d1e7f4a8               │
└──────────────────────────────────────────────────┘

After Privacy Shield:
{
  "post_id": "tiktok_98765",
  "content": "Amazing iPhone 15 for sale! Call me: PHONE_f7e2c9a4b3d5e8f1 Email: EMAIL_a3f5b9c2d1e7f4a8",
  "likes_count": 1500,
  "_anonymized": true,
  "_anonymization_version": "1.0"
}

↓ Sends to enriched.social.anonymized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROCESSOR 2: Context Enricher
┌──────────────────────────────────────────────────┐
│ 🌤️  FETCHING WEATHER...                          │
│ Location: Dhaka                                  │
│ API: OpenWeatherMap                              │
│                                                  │
│ Result:                                          │
│ - Temperature: 28°C                              │
│ - Conditions: Clear                              │
│ - Humidity: 65%                                  │
│                                                  │
│ 📱 DETECTING PRODUCT CATEGORY...                 │
│ Keywords found: "iPhone"                         │
│ Category: smartphone (confidence: 95%)           │
│                                                  │
│ 🕐 ADDING TIME CONTEXT...                        │
│ - Hour: 10 AM                                    │
│ - Day: Monday                                    │
│ - Is Weekend: false                              │
└──────────────────────────────────────────────────┘

After Context Enricher:
{
  "post_id": "tiktok_98765",
  "content": "Amazing iPhone 15...",
  "product_category": "smartphone",
  "category_confidence": 0.95,
  "weather_condition": "Clear",
  "temperature": 28,
  "humidity": 65,
  "is_weekend": false,
  "hour_of_day": 10
}

↓ Sends to enriched.social.contextualized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROCESSOR 3: Embedding Service
┌──────────────────────────────────────────────────┐
│ 🤖 GENERATING AI VECTOR...                       │
│                                                  │
│ Model: all-MiniLM-L6-v2                          │
│ Input: "Amazing iPhone 15 for sale Only 120000  │
│         Taka smartphone Dhaka"                   │
│                                                  │
│ Processing... (takes ~50ms)                      │
│                                                  │
│ Output: 384-dimensional vector                   │
│ [0.234, -0.456, 0.789, 0.123, ..., -0.321]      │
│ (384 numbers total)                              │
└──────────────────────────────────────────────────┘

After Embedding Service:
{
  "post_id": "tiktok_98765",
  "content": "Amazing iPhone 15...",
  "embedding": [0.234, -0.456, 0.789, ...],
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_version": "1.0"
}

↓ Sends to sink.weaviate.vectors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MINUTE 2-3: STORAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STORAGE 1: Snowflake (Analytics)
┌──────────────────────────────────────────────────┐
│ 📊 KAFKA CONNECT SNOWFLAKE SINK                  │
│                                                  │
│ Buffering: Wait for 10,000 records OR 60 seconds │
│ Current buffer: 9,543 records                    │
│                                                  │
│ Buffer full! Flushing to Snowflake...            │
│                                                  │
│ INSERT INTO MILLIONX.RAW_DATA.SOCIAL_POSTS       │
│ VALUES (...10,000 rows...)                       │
│                                                  │
│ ✅ Inserted in 2.3 seconds                       │
│ Cost: ~$0.02 (batched = cheap!)                  │
└──────────────────────────────────────────────────┘

Data now in Snowflake:
┌────────────┬─────────────┬────────────┬───────────┐
│ post_id    │ platform    │ category   │ likes     │
├────────────┼─────────────┼────────────┼───────────┤
│tiktok_98765│ tiktok      │ smartphone │ 1500      │
│tiktok_98766│ tiktok      │ laptop     │ 850       │
│...         │ ...         │ ...        │ ...       │
└────────────┴─────────────┴────────────┴───────────┘

↓ Ready for SQL queries!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STORAGE 2: Weaviate (Vector Search)
┌──────────────────────────────────────────────────┐
│ 🔍 WEAVIATE VECTOR DATABASE                      │
│                                                  │
│ Collection: SocialPost                           │
│ Adding object with vector...                     │
│                                                  │
│ Object ID: uuid-12345-67890                      │
│ Vector dimension: 384                            │
│ HNSW index updated ✓                             │
│                                                  │
│ ✅ Ready for semantic search!                    │
└──────────────────────────────────────────────────┘

↓ Now searchable by meaning, not just keywords!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MINUTE 3+: DATA USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USE CASE 1: Analytics Query (Snowflake)
┌──────────────────────────────────────────────────┐
│ SELECT                                           │
│   product_category,                              │
│   COUNT(*) as post_count,                        │
│   AVG(likes_count) as avg_engagement             │
│ FROM SOCIAL_POSTS                                │
│ WHERE weather_condition = 'Clear'                │
│ GROUP BY product_category                        │
│                                                  │
│ Results:                                         │
│ smartphone  → 3,452 posts, 1,250 avg likes       │
│ laptop      → 1,823 posts, 890 avg likes         │
│ fashion     → 2,134 posts, 2,100 avg likes       │
│                                                  │
│ 💡 Insight: Fashion posts get more engagement    │
│    on sunny days!                                │
└──────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

USE CASE 2: Semantic Search (Weaviate)
┌──────────────────────────────────────────────────┐
│ Query: "cheap smartphone under 20000 taka"       │
│                                                  │
│ Converting query to vector...                    │
│ Searching 50,000 posts by meaning...             │
│ Found 10 similar posts in 23ms!                  │
│                                                  │
│ Top Results:                                     │
│ 1. "Budget-friendly mobile phone 18k BDT" ⭐⭐⭐⭐⭐ │
│ 2. "Affordable phone for students 19500" ⭐⭐⭐⭐   │
│ 3. "Low-cost smartphone great value 21k" ⭐⭐⭐⭐   │
│                                                  │
│ 💡 Note: None contain exact words "cheap" or     │
│    "under 20000" but meanings match!             │
└──────────────────────────────────────────────────┘
```

---

## Comparison: Traditional vs MillionX Pipeline

### Traditional Approach:

```
Manual Data Collection
↓ (Days of work)
Excel Spreadsheet
↓ (Manual analysis)
Basic Insights
↓ (Keyword search only)
Limited Results

Time: Days to weeks
Cost: High labor cost
Scale: Hundreds of records
Search: Exact keyword matches only
Privacy: Manual redaction
```

### MillionX Pipeline:

```
Automated Scrapers
↓ (Minutes)
Kafka Stream
↓ (Real-time processing)
Rich Insights
↓ (AI-powered search)
Deep Analytics

Time: Minutes to hours
Cost: Low automation cost
Scale: Millions of records
Search: Semantic understanding
Privacy: Automatic anonymization
```

---

## The Three Layers Explained Simply

### Layer 1: Collection (The Eyes)

**What it does:** Watches the internet for data
**How:** Automated scrapers run every hour
**Output:** Raw JSON data

### Layer 2: Processing (The Brain)

**What it does:** Cleans, enriches, and understands data
**How:** Stream processors analyze each message
**Output:** Enriched, anonymized, vectorized data

### Layer 3: Storage (The Memory)

**What it does:** Stores data for different purposes
**How:** Snowflake for analytics, Weaviate for AI search
**Output:** Query-ready databases

---

## Mock Data vs Real Data

### With Mock Data (No APIs):

```
mock_data_generator.py
↓ Creates fake posts/orders
↓ Same format as real data
↓ Goes through full pipeline
↓ You see how it works!
```

### With Real APIs (Production):

```
TikTok Scraper (with proxies)
↓ Real posts from TikTok
↓ Requires proxy service ($500/mo)
↓ Full production system
↓ Real insights!
```

**For Learning:** Use mock data
**For Production:** Use real APIs

---

## Performance Numbers

| Stage             | Latency       | Throughput        |
| ----------------- | ------------- | ----------------- |
| Scraper → Kafka   | 100ms         | 100 msgs/sec      |
| Privacy Shield    | <5ms          | 10,000 msgs/sec   |
| Context Enricher  | <20ms         | 5,000 msgs/sec    |
| Embedding Service | <100ms        | 1,000 msgs/sec    |
| Kafka → Snowflake | 60s (batched) | 10,000 rows/batch |
| Weaviate Insert   | <50ms         | 500 vectors/sec   |

**End-to-End:** 2-3 minutes from scraping to searchable

---

## Next: Try It Yourself!

1. Start Kafka: `docker-compose -f docker-compose.kafka.yml up -d`
2. Run mock data: `python mock_data_generator.py`
3. Watch Kafka UI: http://localhost:8080
4. See data flow through topics in real-time!

**You just learned the entire system! 🎉**
