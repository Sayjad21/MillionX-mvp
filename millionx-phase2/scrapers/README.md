# MillionX Phase 2 - Scraper Agents

Production-grade data collection system with anti-bot hardening, schema validation, and dead letter queue handling.

## 📁 Structure

```
scrapers/
├── shared/           # Shared utilities
│   ├── kafka_producer.py    # Kafka client with retries
│   ├── dlq_handler.py        # Dead Letter Queue routing
│   ├── models.py             # Pydantic schemas
│   └── config.py             # Configuration management
├── social/           # Social media scrapers
│   ├── tiktok_scraper.py     # TikTok with proxy rotation
│   └── facebook_scraper.py   # Facebook Graph API
├── market/           # E-commerce integrations
│   ├── shopify_integration.py
│   └── daraz_integration.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required Configuration:**
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address
- `PROXY_LIST` - Proxy servers for TikTok scraping (optional but recommended)
- `FACEBOOK_ACCESS_TOKEN` - For Facebook scraper
- `SHOPIFY_ACCESS_TOKEN` - For Shopify integration
- `DARAZ_APP_KEY` - For Daraz integration

### 2. Install Dependencies

```bash
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Run Scrapers

```bash
# TikTok scraper
python social/tiktok_scraper.py

# Facebook scraper
python social/facebook_scraper.py

# Shopify integration
python market/shopify_integration.py

# Daraz integration
python market/daraz_integration.py
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t millionx-scrapers:latest .
```

### Run Containers

```bash
# TikTok scraper
docker run --env-file .env millionx-scrapers:latest python social/tiktok_scraper.py

# Facebook scraper
docker run --env-file .env millionx-scrapers:latest python social/facebook_scraper.py

# Shopify integration
docker run --env-file .env millionx-scrapers:latest python market/shopify_integration.py
```

## ☸️ Kubernetes CronJob Deployment

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: tiktok-scraper
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scraper
            image: millionx-scrapers:latest
            command: ["python", "social/tiktok_scraper.py"]
            envFrom:
            - secretRef:
                name: scraper-secrets
          restartPolicy: OnFailure
```

## 🔐 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | Yes | localhost:9092 |
| `PROXY_LIST` | Comma-separated proxy URLs | No | - |
| `TIKTOK_KEYWORDS` | Search keywords for TikTok | No | smartphone,laptop,... |
| `TIKTOK_MAX_POSTS` | Max posts per run | No | 50 |
| `FACEBOOK_ACCESS_TOKEN` | Facebook API token | For FB | - |
| `SHOPIFY_ACCESS_TOKEN` | Shopify API token | For Shopify | - |
| `DARAZ_APP_KEY` | Daraz API key | For Daraz | - |
| `LOG_LEVEL` | Logging level | No | INFO |

### Proxy Configuration

**Format:**
```
PROXY_LIST=http://user:pass@proxy1.com:8080,http://user:pass@proxy2.com:8080
```

**Recommended Providers:**
- [BrightData](https://brightdata.com) - Residential proxies
- [Smartproxy](https://smartproxy.com) - Datacenter + residential
- [Oxylabs](https://oxylabs.io) - Enterprise-grade

## 📊 Data Flow

```
Scraper → Validation (Pydantic) → Kafka Topic → Stream Processors
                ↓ (if fails)
         Dead Letter Queue (DLQ)
```

### Kafka Topics

- `source.social.tiktok` - TikTok posts
- `source.social.facebook` - Facebook posts
- `source.market.shopify` - Shopify orders
- `source.market.daraz` - Daraz orders
- `dead-letters-social` - Failed social posts
- `dead-letters-market` - Failed market orders
- `schema-validation-errors` - Schema failures

## 🛡️ Anti-Bot Features

### TikTok Scraper
- ✅ Rotating proxy pool
- ✅ Random user agent rotation
- ✅ Human-like delays (3-8s)
- ✅ Browser fingerprint hiding
- ✅ Stealth mode Playwright

### Facebook Scraper
- ✅ Official Graph API (no scraping)
- ✅ OAuth 2.0 authentication
- ✅ Rate limiting compliance

### Shopify/Daraz
- ✅ Official REST APIs
- ✅ HMAC signature authentication
- ✅ Automatic rate limiting

## 🔍 Monitoring

### Health Checks

```bash
# Test Kafka connectivity
python -c "from shared.kafka_producer import KafkaProducerClient; print('✅ Kafka OK')"

# Validate config
python shared/config.py

# Test scraper
python social/tiktok_scraper.py --dry-run
```

### Key Metrics to Monitor

1. **Success Rate**: `scraper_success_count / scraper_total_attempts`
2. **DLQ Rate**: `dlq_messages / total_messages` (target: <2%)
3. **Proxy Failures**: Track HTTP 403/429 errors
4. **Schema Validation Rate**: Track Pydantic validation failures

## 🚨 Troubleshooting

### Issue: TikTok Returns 403 Forbidden

**Cause:** IP blocked or proxy detected

**Solutions:**
1. Rotate proxies more frequently
2. Increase delay between requests
3. Switch proxy provider
4. Consider Apify fallback

### Issue: Schema Validation Failures

**Cause:** Missing required fields or data type mismatch

**Solution:**
```bash
# Check DLQ messages
docker exec millionx-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic schema-validation-errors \
  --from-beginning --max-messages 10
```

### Issue: Kafka Connection Refused

**Cause:** Kafka not running or wrong broker address

**Solution:**
```bash
# Verify Kafka is running
docker ps | grep kafka

# Test connectivity
telnet localhost 9092

# Check KAFKA_BOOTSTRAP_SERVERS in .env
```

## 📚 API Documentation

### TikTok Scraper API

```python
from social.tiktok_scraper import TikTokScraper

scraper = TikTokScraper(keywords=["smartphone", "laptop"])
await scraper.scrape()  # Returns: scraped_count, failed_count
```

### Facebook Scraper API

```python
from social.facebook_scraper import FacebookScraper

scraper = FacebookScraper(page_ids=["123456789"])
scraper.scrape_all_pages()
```

### Shopify Integration API

```python
from market.shopify_integration import ShopifyIntegration

integration = ShopifyIntegration()
integration.run_sync(limit=250)
```

## 🔄 Development Workflow

### Running Tests

```bash
# TODO: Add pytest tests in Week 3
pytest tests/
```

### Local Development

```bash
# Start Kafka locally
cd ../
docker-compose -f docker-compose.kafka.yml up -d

# Run scraper with debug logging
LOG_LEVEL=DEBUG python social/tiktok_scraper.py
```

### Code Style

```bash
# Format code
black .

# Lint
pylint shared/ social/ market/
```

## 📞 Support

- **Bugs:** Create GitHub issue
- **Questions:** Slack #millionx-data-eng
- **Urgent Issues:** Page on-call engineer

---

**Last Updated:** December 20, 2025  
**Maintained By:** Data Engineering Team  
**Version:** 1.0.0
