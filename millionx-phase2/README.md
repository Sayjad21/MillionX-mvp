# MillionX Phase 2 - Data Pipeline

## 🎯 Overview
Production-grade data engineering pipeline for AI-driven commerce insights.

**Status:** Week 1 - Kafka Infrastructure Setup

## 📁 Project Structure

```
millionx-phase2/
├── docker-compose.kafka.yml    # Kafka stack with monitoring
├── prometheus.yml              # Prometheus configuration
├── kafka-topics.sh             # Topic creation script
├── kafka-connect-snowflake.json # Snowflake sink config
├── scrapers/
│   ├── social/                 # TikTok/Facebook scrapers
│   ├── market/                 # Shopify/Daraz integrations
│   └── shared/                 # Shared utilities
├── stream-processors/          # Faust stream processors
├── k8s/                        # Kubernetes manifests
└── kafka-connect-plugins/      # Kafka Connect plugins
```

## 🚀 Quick Start

### Step 1: Start Kafka Stack
```bash
cd millionx-phase2

# Start all services
docker-compose -f docker-compose.kafka.yml up -d

# Check status
docker ps | grep millionx
```

### Step 2: Create Kafka Topics
```bash
# Windows (PowerShell)
bash kafka-topics.sh

# Or manually with PowerShell
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Step 3: Access Services
- **Kafka UI:** http://localhost:8080
- **Grafana:** http://localhost:3001 (admin/admin123)
- **Prometheus:** http://localhost:9090
- **Kafka Connect:** http://localhost:8083
- **Weaviate:** http://localhost:8082

## 📊 Topics Created

### Source Topics (Raw Ingestion)
- `source.social.tiktok` - TikTok posts (6 partitions, 7 days retention)
- `source.social.facebook` - Facebook posts (6 partitions, 7 days retention)
- `source.market.shopify` - Shopify orders (4 partitions, 7 days retention)
- `source.market.daraz` - Daraz orders (4 partitions, 7 days retention)
- `context.weather` - Weather data (2 partitions, 30 days retention)

### Sink Topics (Processed Data)
- `sink.snowflake.orders` - Structured data for Snowflake
- `sink.weaviate.vectors` - Anonymized data for vectorization
- `enriched.weaviate.vectors` - Enriched data ready for embedding

### Dead Letter Queues
- `dead-letters-social` - Failed social media messages
- `dead-letters-market` - Failed marketplace messages

## 🔍 Health Checks

### Check Kafka Topics
```powershell
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Check Consumer Groups
```powershell
docker exec millionx-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

### Check Kafka Connect Status
```powershell
curl http://localhost:8083/connectors | ConvertFrom-Json
```

### Test Message Production
```powershell
# Send test message
docker exec millionx-kafka kafka-console-producer `
  --bootstrap-server localhost:9092 `
  --topic source.social.tiktok

# Type a message and press Ctrl+C to exit
```

### Test Message Consumption
```powershell
# Consume messages
docker exec millionx-kafka kafka-console-consumer `
  --bootstrap-server localhost:9092 `
  --topic source.social.tiktok `
  --from-beginning
```

## 📚 Next Steps

### Week 1: Kafka Infrastructure ✅
- [x] Deploy Kafka cluster
- [x] Create topics
- [x] Setup monitoring
- [ ] Validate end-to-end connectivity

### Week 2: Scraper Agents (Coming Next)
- [ ] Build TikTok scraper with proxy rotation
- [ ] Build Facebook scraper
- [ ] Implement Shopify integration
- [ ] Implement Daraz integration
- [ ] Setup Dead Letter Queue handlers

### Week 3: Stream Processing (Planned)
- [ ] Privacy Shield (PII anonymization)
- [ ] Context Enricher
- [ ] Embedding Service

### Week 4: Storage & Optimization (Planned)
- [ ] Snowflake integration
- [ ] Weaviate setup
- [ ] Cost optimization
- [ ] Performance tuning

## 🛠️ Configuration

### Environment Variables
Create a `.env` file for sensitive configuration:

```bash
# Snowflake (for Week 4)
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=KAFKA_CONNECTOR
SNOWFLAKE_PRIVATE_KEY=/path/to/key
SNOWFLAKE_PASSWORD=your_password

# Proxy Configuration (for Week 2)
PROXY_LIST=http://user:pass@proxy1:8080,http://user:pass@proxy2:8080

# API Keys (for Week 2)
APIFY_TOKEN=apify_api_xyz123
OPENWEATHER_API_KEY=your_weather_api_key
```

## 🚨 Troubleshooting

### Issue: Kafka won't start
```powershell
# Check logs
docker logs millionx-kafka

# Check if ports are in use
netstat -ano | findstr :9092
netstat -ano | findstr :2181
```

### Issue: Topics not created
```powershell
# Manually create a topic
docker exec millionx-kafka kafka-topics --create `
  --topic test-topic `
  --partitions 1 `
  --replication-factor 1 `
  --bootstrap-server localhost:9092
```

### Issue: Kafka Connect not starting
```powershell
# Check Kafka Connect logs
docker logs millionx-kafka-connect

# Verify plugin directory
docker exec millionx-kafka-connect ls /usr/share/confluent-hub-components
```

## 📖 Documentation

- **Full Implementation Plan:** [../phase2-implementation.md](../phase2-implementation.md)
- **Production Hardening:** [../PHASE2-PRODUCTION-HARDENING.md](../PHASE2-PRODUCTION-HARDENING.md)
- **Quick Reference:** [../PHASE2-QUICK-REFERENCE.md](../PHASE2-QUICK-REFERENCE.md)

## 🎯 Success Criteria

| Metric | Target | Current Status |
|--------|--------|----------------|
| Kafka Uptime | >99.5% | Monitoring started |
| Topic Count | 10 topics | ✅ Complete |
| Monitoring | Prometheus + Grafana | ✅ Complete |
| Kafka Connect | Deployed | ✅ Complete |

---

**Last Updated:** December 20, 2025  
**Current Phase:** Week 1 - Kafka Infrastructure  
**Next Milestone:** Build scraper agents with anti-bot hardening
