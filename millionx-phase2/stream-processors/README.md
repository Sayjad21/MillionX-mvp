# Stream Processors - Real-Time Data Pipeline

[![Phase 2 Week 3](https://img.shields.io/badge/Phase%202-Week%203-green)](https://github.com/Sayjad21/MillionX-mvp)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Faust](https://img.shields.io/badge/Faust-0.10.0-orange)](https://faust-streaming.github.io/)

Real-time stream processing layer for MillionX data pipeline, built with Faust (Kafka Streams for Python).

---

## 🎯 Overview

This module implements 4 critical stream processors that transform raw scraped data into AI-ready insights:

| Processor | Purpose | Latency Target |
|-----------|---------|----------------|
| **Privacy Shield** | PII anonymization with SHA-256 hashing | <5ms |
| **Context Enricher** | Product metadata + weather + temporal context | <20ms |
| **Embedding Service** | Generate 384-dim vectors for semantic search | <100ms (P95) |
| **Schema Validator** | Pydantic validation with DLQ routing | <3ms |

**Total Pipeline Latency:** <5 seconds (end-to-end, from scraper to Weaviate)

---

## 📂 Project Structure

```
stream-processors/
├── shared/
│   ├── __init__.py
│   ├── faust_config.py       # Centralized Faust configuration
│   └── metrics.py             # Prometheus metrics collection
├── privacy_shield.py          # PII anonymization processor
├── context_enricher.py        # Context enrichment processor
├── embedding_service.py       # Vector embedding generation
├── schema_validator.py        # Schema validation layer
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Multi-processor orchestration
├── .env.example               # Environment variables template
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Kafka cluster running (from Week 1)
- Redis (for caching)
- Weaviate (for vector storage)

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Variables:**
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
PRIVACY_SALT=CHANGE_THIS_IN_PRODUCTION  # ⚠️ CRITICAL: Use secrets manager
WEATHER_API_KEY=your_openweathermap_key  # Get free key: https://openweathermap.org/api
WEAVIATE_URL=http://localhost:8082
```

### 2. Start Stream Processors

```bash
# Build Docker images
docker-compose build

# Start all processors
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Verify Health

```bash
# Check all processors are running
docker-compose ps

# Test Faust web UI
curl http://localhost:6066/health  # Privacy Shield
curl http://localhost:6067/health  # Context Enricher
curl http://localhost:6068/health  # Embedding Service
curl http://localhost:6069/health  # Schema Validator
```

---

## 🛡️ Privacy Shield

**Purpose:** Anonymize PII (Personally Identifiable Information) in real-time.

### Features

- **Regex-based PII Detection:**
  - Phone numbers (Bangladesh & US formats)
  - Email addresses
  - Names (capitalized patterns)
  - Credit card numbers
  - Bangladesh National IDs

- **SHA-256 Hashing:**
  - All PII replaced with `HASH_TYPE_<hash>`
  - Example: `john.doe@email.com` → `EMAIL_a3f5b9c2d1e7f4a8`
  - Salt-based hashing (configurable via `PRIVACY_SALT`)

- **Preserves Data Utility:**
  - Original data structure maintained
  - Non-PII fields untouched
  - Metadata added: `_anonymized`, `_anonymization_version`

### Data Flow

```
source.social.tiktok
source.social.facebook    →  [Privacy Shield]  →  enriched.social.anonymized
source.market.shopify                           →  enriched.market.anonymized
source.market.daraz
```

### Configuration

```env
PRIVACY_SALT=your_secret_salt_keep_this_secret
PII_HASH_LENGTH=16  # Truncated hash length
```

### Run Standalone

```bash
faust -A privacy_shield worker -l info
```

---

## 🌍 Context Enricher

**Purpose:** Enrich data with product metadata, weather, and temporal context.

### Features

#### 1. Product Category Detection
- Keyword-based matching (expandable via database)
- Categories: `smartphone`, `laptop`, `fashion`, `electronics`, `home`, `general`
- Confidence scoring (placeholder for ML model)

#### 2. Weather Enrichment
- OpenWeatherMap API integration
- Bangladesh cities supported: Dhaka, Chittagong, Sylhet, Rajshahi, Khulna
- Redis caching (30-minute TTL)
- Fields: `temperature`, `humidity`, `conditions`, `wind_speed`, `is_extreme_weather`

#### 3. Temporal Context
- Hour of day, day of week, season
- Business hours detection (9 AM - 5 PM)
- Weekend flagging
- Bangladesh climate seasons: winter, summer, monsoon, autumn

### Data Flow

```
enriched.social.anonymized
enriched.market.anonymized  →  [Context Enricher]  →  enriched.social.contextualized
                                                    →  enriched.market.contextualized
```

### Configuration

```env
REDIS_HOST=localhost
REDIS_PORT=6379
WEATHER_API_KEY=your_openweathermap_key
WEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather
```

### Run Standalone

```bash
faust -A context_enricher worker -l info
```

---

## 🧠 Embedding Service

**Purpose:** Generate vector embeddings for semantic search and recommendations.

### Features

- **Sentence-Transformers Integration:**
  - Model: `all-MiniLM-L6-v2` (384-dimensional embeddings)
  - Optimized for semantic similarity
  - Supports GPU acceleration (`EMBEDDING_DEVICE=cuda`)

- **Batch Processing:**
  - Configurable batch size (default: 100 messages)
  - Automatic flushing every 30 seconds
  - Target latency: <100ms P95

- **Weaviate Integration:**
  - Automatic object creation with vectors
  - Collections: `SocialPost`, `MarketOrder`
  - Full record stored as `raw_data` for retrieval

### Data Flow

```
enriched.social.contextualized
enriched.market.contextualized  →  [Embedding Service]  →  sink.snowflake.social
                                                         →  sink.snowflake.market
                                   ↓
                               Weaviate Vector DB
```

### Configuration

```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=100
EMBEDDING_MAX_LENGTH=512
EMBEDDING_DEVICE=cpu  # Use 'cuda' for GPU
WEAVIATE_URL=http://localhost:8082
```

### Run Standalone

```bash
faust -A embedding_service worker -l info
```

---

## ✅ Schema Validator

**Purpose:** Validate all incoming data against Pydantic schemas before processing.

### Features

- **Pydantic Validation:**
  - Schemas: `SocialPost`, `MarketOrder`
  - Field type checking, min/max constraints, enum validation
  - Custom validators (e.g., `total_price = quantity * unit_price`)

- **Automatic DLQ Routing:**
  - Failed validations → `schema-validation-errors` topic
  - Error metadata: type, message, timestamp
  - Retry count tracking

- **Real-Time Metrics:**
  - Total validated, passed, failed
  - Pass rate percentage
  - Failure type breakdown

### Data Flow

```
source.social.tiktok
source.social.facebook    →  [Schema Validator]  →  validated.social.tiktok
source.market.shopify                            →  validated.social.facebook
source.market.daraz                              →  validated.market.shopify
                                                 →  validated.market.daraz
                             ↓ (failures)
                     schema-validation-errors (DLQ)
```

### Configuration

```env
# No special configuration required
# Uses Pydantic models from ../scrapers/shared/models.py
```

### Run Standalone

```bash
faust -A schema_validator worker -l info
```

---

## 📊 Monitoring & Metrics

### Faust Web UI

Each processor exposes a web interface:

- **Privacy Shield:** http://localhost:6066
- **Context Enricher:** http://localhost:6067
- **Embedding Service:** http://localhost:6068
- **Schema Validator:** http://localhost:6069

### Key Metrics

#### Privacy Shield
- `messages_processed` - Total anonymized messages
- `processing_latency_ms` - P50/P95/P99 latency
- `dlq_sent` - Failed anonymizations

#### Context Enricher
- `cache_hit_rate` - Redis cache efficiency
- `weather_api_calls` - External API usage
- `enrichment_latency_ms` - Enrichment time

#### Embedding Service
- `batch_size` - Current batch size
- `embedding_latency_ms` - Vector generation time
- `weaviate_write_success_rate` - Storage success rate

#### Schema Validator
- `validation_pass_rate` - % of valid messages
- `failure_types` - Breakdown by error type
- `dlq_rate` - % of messages sent to DLQ

### Prometheus Integration

Metrics are exported via Faust web interface and can be scraped by Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'faust-privacy-shield'
    static_configs:
      - targets: ['localhost:6066']
  
  - job_name: 'faust-context-enricher'
    static_configs:
      - targets: ['localhost:6067']
  
  - job_name: 'faust-embedding-service'
    static_configs:
      - targets: ['localhost:6068']
  
  - job_name: 'faust-schema-validator'
    static_configs:
      - targets: ['localhost:6069']
```

---

## 🔧 Configuration Reference

### Kafka Settings

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Comma-separated for clusters
FAUST_PRODUCER_ACKS=-1                  # All replicas (most durable)
FAUST_PRODUCER_COMPRESSION=gzip         # Bandwidth optimization
```

### Performance Tuning

```env
FAUST_STREAM_BUFFER_MAXSIZE=4096       # Stream buffer size
FAUST_STREAM_WAIT_EMPTY=true           # Wait for buffer before processing
EMBEDDING_BATCH_SIZE=100               # Batch size for embeddings
```

### Security

```env
PRIVACY_SALT=USE_SECRETS_MANAGER_IN_PROD  # ⚠️ NEVER commit to git
REDIS_PASSWORD=your_redis_password         # If Redis requires auth
WEAVIATE_API_KEY=your_weaviate_key        # If Weaviate requires auth
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t millionx-stream-processor:latest .
```

### Run Single Processor

```bash
docker run -d \
  --name privacy-shield \
  --network millionx-network \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e PRIVACY_SALT=your_secret_salt \
  -p 6066:6066 \
  millionx-stream-processor:latest \
  faust -A privacy_shield worker -l info
```

### Multi-Processor Stack

```bash
# Start all processors + dependencies
docker-compose up -d

# Scale embedding service for higher throughput
docker-compose up -d --scale embedding-service=3

# View resource usage
docker stats

# Restart specific processor
docker-compose restart privacy-shield
```

---

## 🧪 Testing

### Unit Tests (Example)

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Integration Tests

```bash
# Test privacy shield with sample data
echo '{"post_id": "test_123", "platform": "tiktok", "content": "Check out my new phone! Contact me at john.doe@email.com or +880123456789", "author": "John Doe", "engagement_count": 100, "posted_at": "2025-12-20T10:00:00Z"}' | \
  docker exec -i millionx-kafka kafka-console-producer \
  --broker-list localhost:9092 \
  --topic source.social.tiktok

# Verify anonymized output
docker exec millionx-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic enriched.social.anonymized \
  --from-beginning \
  --max-messages 1
```

### Load Testing

```bash
# Generate 10,000 test messages
python scripts/load_test.py --messages 10000 --topic source.social.tiktok

# Monitor latency in Grafana
# Open: http://localhost:3001
```

---

## 🚨 Troubleshooting

### Issue: High DLQ Rate (>2%)

**Diagnosis:**
```bash
# Inspect DLQ messages
docker exec millionx-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic schema-validation-errors \
  --from-beginning \
  --max-messages 10
```

**Common Causes:**
- Missing required fields in scrapers
- Data type mismatches (e.g., string in int field)
- Schema version mismatch

**Solution:**
- Update Pydantic models in `scrapers/shared/models.py`
- Fix scraper output format
- Replay DLQ messages after fix: `python scripts/dlq_replayer.py`

### Issue: Context Enricher Weather API Timeout

**Diagnosis:**
```bash
docker logs millionx-context-enricher | grep "Weather API"
```

**Solution:**
- Verify API key: `curl "http://api.openweathermap.org/data/2.5/weather?lat=23.8103&lon=90.4125&appid=$WEATHER_API_KEY"`
- Increase timeout in `context_enricher.py`
- Check Redis cache hit rate (should be >80%)

### Issue: Embedding Service High Memory Usage

**Symptoms:** Container OOM killed

**Solution:**
```bash
# Increase memory limit in docker-compose.yml
embedding-service:
  mem_limit: 4g  # Increase from 2g

# Or use smaller embedding model
EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2  # 16-dim vectors
```

---

## 📚 Additional Resources

### Faust Documentation
- Official Docs: https://faust-streaming.github.io/
- GitHub: https://github.com/faust-streaming/faust

### Sentence-Transformers
- Documentation: https://www.sbert.net/
- Model Hub: https://huggingface.co/sentence-transformers

### Weaviate
- Documentation: https://weaviate.io/developers/weaviate
- Python Client: https://weaviate-python-client.readthedocs.io/

### OpenWeatherMap API
- API Docs: https://openweathermap.org/api
- Free Tier: 1,000 calls/day (sufficient for development)

---

## 🎓 Architecture Insights

### Why Faust?

1. **Native Kafka Integration:** Built on Kafka Streams concepts
2. **Python Native:** Async/await support, Pydantic integration
3. **Stateful Processing:** RocksDB for windowing and aggregations
4. **Simple Deployment:** Docker-friendly, no JVM required

### Data Flow Summary

```
Scrapers (Week 2)
    ↓
[Schema Validator] ← Real-time validation
    ↓
[Privacy Shield] ← PII anonymization
    ↓
[Context Enricher] ← Weather + Product metadata
    ↓
[Embedding Service] ← Vector generation
    ↓
┌────────────────┬─────────────────┐
│                │                 │
Weaviate         Snowflake        DLQ Topics
(Vectors)        (Archival)       (Failures)
```

---

## 🚀 Next Steps - Week 4

### 1. Snowflake Integration
- Deploy Kafka Connect Snowflake Sink Connector
- Test SNOWPIPE_STREAMING mode
- Validate batch uploads (10K records/batch)

### 2. Weaviate Schema
- Define collections: `SocialPost`, `MarketOrder`
- Configure text2vec-transformers
- Build similarity search queries

### 3. Performance Optimization
- GPU acceleration for embedding service
- Kafka partition rebalancing
- Consumer group lag tuning
- Cost optimization (Snowflake credits)

---

## 📝 Files Created (Week 3)

```
stream-processors/
├── shared/
│   ├── __init__.py                ✅ Module marker
│   ├── faust_config.py           ✅ Configuration (150 lines)
│   └── metrics.py                ✅ Metrics collection (120 lines)
├── privacy_shield.py             ✅ PII anonymization (420 lines)
├── context_enricher.py           ✅ Context enrichment (450 lines)
├── embedding_service.py          ✅ Vector generation (380 lines)
├── schema_validator.py           ✅ Schema validation (350 lines)
├── requirements.txt              ✅ Python dependencies
├── Dockerfile                    ✅ Production image
├── docker-compose.yml            ✅ Multi-processor stack
├── .env.example                  ✅ Configuration template
└── README.md                     ✅ Documentation (this file)

Total: 10 files, ~2,070 lines of code
```

---

**Status:** ✅ **Week 3 Complete**  
**Next:** Week 4 - Storage & Optimization  
**Target Date:** December 27, 2025
