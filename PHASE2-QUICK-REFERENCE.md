# Phase 2: Quick Reference Guide

## 🚀 Environment Setup

### 1. Proxy Configuration (Required for Scrapers)
```bash
# Option A: BrightData (Recommended)
export PROXY_LIST="http://user-sp-<zone>:pass@brd.superproxy.io:22225"

# Option B: Smartproxy
export PROXY_LIST="http://user:pass@gate.smartproxy.com:7000"

# Option C: Multiple rotating proxies
export PROXY_LIST="http://user:pass@proxy1:8080,http://user:pass@proxy2:8080"
```

### 2. Snowflake Configuration
```bash
# For Kafka Connect
export SNOWFLAKE_USER="KAFKA_CONNECTOR"
export SNOWFLAKE_PRIVATE_KEY="<path_to_rsa_key>"
export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"

# For Python batch loader (alternative)
export SNOWFLAKE_PASSWORD="<password>"
```

### 3. Optional: Apify Fallback
```bash
export APIFY_TOKEN="apify_api_xyz123"
```

---

## 📋 Deployment Commands

### Start Full Phase 2 Stack
```bash
# 1. Start Kafka + monitoring
docker-compose -f docker-compose.kafka.yml up -d

# 2. Create topics
chmod +x kafka-topics.sh && ./kafka-topics.sh

# 3. Deploy Kafka Connect + Snowflake Sink
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @kafka-connect-snowflake.json

# 4. Build and deploy scrapers (K8s CronJob)
kubectl apply -f k8s/tiktok-scraper-cronjob.yaml

# 5. Start Faust stream processors
faust -A privacy_shield worker -l info &
faust -A context_enricher worker -l info &
faust -A embedding_service worker -l info &

# 6. Deploy Weaviate
docker-compose -f docker-compose.kafka.yml up -d weaviate
python weaviate_schema.py  # Create schema
```

---

## 🔍 Health Checks

### Kafka
```bash
# List topics
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer lag
docker exec millionx-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group snowflake-sink

# UI dashboard
open http://localhost:8080
```

### Kafka Connect (Snowflake Sink)
```bash
# Check connector status
curl http://localhost:8083/connectors/snowflake-sink-orders/status | jq

# View connector config
curl http://localhost:8083/connectors/snowflake-sink-orders | jq

# Restart if failed
curl -X POST http://localhost:8083/connectors/snowflake-sink-orders/restart
```

### Scrapers
```bash
# Check last run (K8s CronJob)
kubectl get pods -l app=tiktok-scraper --sort-by=.metadata.creationTimestamp

# View logs
kubectl logs -f <pod-name>

# Manually trigger
kubectl create job --from=cronjob/tiktok-scraper manual-scrape-1
```

### Snowflake
```sql
-- Check recent ingestion
SELECT 
  COUNT(*) as row_count,
  MAX(ingestion_time) as last_ingestion
FROM MILLIONX.RAW_DATA.ORDERS
WHERE ingestion_time > DATEADD(hour, -1, CURRENT_TIMESTAMP());

-- Check ingestion rate (last hour)
SELECT 
  DATE_TRUNC('minute', ingestion_time) as minute,
  COUNT(*) as records
FROM MILLIONX.RAW_DATA.ORDERS
WHERE ingestion_time > DATEADD(hour, -1, CURRENT_TIMESTAMP())
GROUP BY minute
ORDER BY minute DESC;

-- Monitor warehouse credit usage (cost tracking)
SELECT 
  start_time,
  end_time,
  credits_used,
  credits_used * 2.5 as estimated_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
  AND warehouse_name = 'COMPUTE_WH'
ORDER BY start_time DESC;
```

### Weaviate
```bash
# Check schema
curl http://localhost:8082/v1/schema | jq

# Check object count
curl http://localhost:8082/v1/objects | jq '.totalResults'

# Test semantic search
curl -X POST http://localhost:8082/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ Get { SocialPost(nearText: {concepts: [\"cheap phone\"]}) { content platform engagement_count }}}"
  }' | jq
```

---

## 🚨 Troubleshooting

### Issue: Scraper Getting Blocked (403/429 errors)
```bash
# 1. Verify proxy is working
curl --proxy $PROXY_LIST https://api.ipify.org

# 2. Check proxy rotation
grep "proxy" /var/log/scrapers/tiktok.log | tail -20

# 3. Increase delay between requests
# Edit tiktok_scraper.py: await asyncio.sleep(random.uniform(5, 10))

# 4. If still blocked, switch to Apify
export USE_APIFY=true
```

### Issue: Snowflake Costs Too High
```sql
-- Check if batching is working
SELECT 
  DATE_TRUNC('hour', ingestion_time) as hour,
  COUNT(*) as records,
  COUNT(*) / 60.0 as avg_per_minute
FROM MILLIONX.RAW_DATA.ORDERS
WHERE ingestion_time > DATEADD(day, -1, CURRENT_TIMESTAMP())
GROUP BY hour
ORDER BY hour DESC;

-- Expected: 10,000+ records per batch (1-2 batches per minute)
-- Red flag: <100 records per minute (indicates row-by-row inserts)
```

```bash
# If batching is not working:
# 1. Check Kafka Connect buffer settings
curl http://localhost:8083/connectors/snowflake-sink-orders/config | jq '.["buffer.count.records"]'
# Should be: "10000"

# 2. Verify Snowpipe Streaming is enabled
curl http://localhost:8083/connectors/snowflake-sink-orders/config | jq '.["snowflake.ingestion.method"]'
# Should be: "SNOWPIPE_STREAMING"

# 3. If still issues, switch to Pandas batch loader
cd scrapers && python snowflake_batch_sink.py
```

### Issue: High DLQ Rate (>2%)
```bash
# 1. Inspect DLQ messages
docker exec millionx-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dead-letters-social \
  --from-beginning \
  --max-messages 10

# 2. Common causes:
# - Schema validation failures (check Pydantic models)
# - Missing required fields (update scrapers)
# - Invalid data types (e.g., string in int field)

# 3. Fix and replay DLQ
# Create a consumer that reads DLQ, fixes issues, and republishes
python scripts/dlq_replayer.py --topic dead-letters-social
```

### Issue: Kafka Connect Not Starting
```bash
# 1. Check logs
docker logs millionx-kafka-connect

# 2. Verify Snowflake connector is installed
docker exec millionx-kafka-connect ls /usr/share/confluent-hub-components

# 3. If missing, install manually
docker exec millionx-kafka-connect confluent-hub install \
  snowflakeinc/snowflake-kafka-connector:2.0.0

# 4. Restart Kafka Connect
docker-compose -f docker-compose.kafka.yml restart kafka-connect
```

---

## 📊 Key Metrics Dashboard

Open Grafana: http://localhost:3001 (admin/admin123)

**Critical Panels to Monitor:**

1. **Scraper Success Rate** (Target: >95%)
   - Query: `rate(scraper_success_total[5m]) / rate(scraper_attempts_total[5m])`

2. **Kafka Lag** (Alert if >10,000)
   - Query: `kafka_consumergroup_lag{consumergroup="snowflake-sink"}`

3. **DLQ Rate** (Alert if >2%)
   - Query: `rate(kafka_topic_partition_current_offset{topic=~"dead-letters-.*"}[5m])`

4. **Snowflake Daily Cost** (Alert if >$15)
   - Query: `sum(snowflake_credits_used) * 2.5`

5. **Embedding Latency P95** (Target: <100ms)
   - Query: `histogram_quantile(0.95, rate(embedding_duration_seconds_bucket[5m]))`

---

## 🔐 Security Checklist

- [ ] Rotate Kafka SASL/SSL credentials (use secret manager)
- [ ] Enable Snowflake MFA for connector user
- [ ] Whitelist Kafka Connect IPs in Snowflake
- [ ] Store proxy credentials in Kubernetes secrets (not env vars)
- [ ] Enable TLS for Kafka (in production)
- [ ] Setup VPC peering for Kafka ↔ Snowflake traffic
- [ ] Implement rate limiting on webhook endpoints
- [ ] Regular security audits on PII hashing implementation

---

## 📞 Emergency Contacts

| Issue | Contact | Escalation Path |
|-------|---------|----------------|
| Kafka Down | Data Eng Lead | Infra Team → CTO |
| Snowflake Cost Spike | FinOps | Finance Director → CFO |
| Scraper IP Banned | DevOps | Proxy Provider Support |
| DLQ Overflow | Data Quality Lead | Data Eng Lead → VP Eng |
| Production Incident | On-Call Eng | Incident Commander → CTO |

---

## 📚 Documentation Links

- **Phase 2 Full Plan:** [phase2-implementation.md](./phase2-implementation.md)
- **Production Hardening:** [PHASE2-PRODUCTION-HARDENING.md](./PHASE2-PRODUCTION-HARDENING.md)
- **Kafka Topic Design:** [phase2-implementation.md#kafka-topic-hierarchy](./phase2-implementation.md)
- **Runbooks:** `/docs/runbooks/` (create after Week 2)
- **Incident Postmortems:** `/docs/postmortems/` (create as needed)

---

**Last Updated:** December 20, 2025  
**Maintained By:** Data Engineering Team  
**Review Cadence:** Weekly during Phase 2, Monthly after Phase 3
