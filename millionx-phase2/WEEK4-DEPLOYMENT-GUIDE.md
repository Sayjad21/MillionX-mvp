# Week 4 Deployment Guide: Storage & Monitoring

Complete deployment guide for MillionX Phase 2 Week 4 components: Snowflake, Weaviate, Weather Fetcher, and Monitoring.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [1. Snowflake Deployment](#1-snowflake-deployment)
- [2. Weaviate Deployment](#2-weaviate-deployment)
- [3. Weather Fetcher Deployment](#3-weather-fetcher-deployment)
- [4. Monitoring Deployment](#4-monitoring-deployment)
- [5. Validation & Testing](#5-validation--testing)
- [6. Troubleshooting](#6-troubleshooting)

---

## Prerequisites

### Required Services (from Week 1)
- ✅ Kafka cluster running (localhost:9092)
- ✅ Zookeeper running
- ✅ Kafka Connect running (localhost:8083)
- ✅ Prometheus running (localhost:9090)
- ✅ Grafana running (localhost:3000)
- ✅ Weaviate running (localhost:8080)

### Required Accounts
- **Snowflake Account**: Trial or paid account
- **OpenWeatherMap API Key**: Free tier (60 calls/min)

### Tools
- Docker & Docker Compose
- Python 3.11+
- kubectl (for Kubernetes deployment)
- snowsql CLI (optional, for manual testing)

---

## 1. Snowflake Deployment

### 1.1 Create Snowflake Account

1. Sign up at https://signup.snowflake.com/ (30-day free trial)
2. Note your account identifier: `<account>.<region>.snowflakecomputing.com`
3. Create a user with appropriate permissions

### 1.2 Initialize Database Schema

```bash
# Navigate to snowflake directory
cd millionx-phase2/snowflake

# Option 1: Using snowsql CLI
snowsql -a <account> -u <username> -f schema-setup.sql

# Option 2: Using Snowflake Web UI
# 1. Login to https://<account>.snowflakecomputing.com
# 2. Go to Worksheets
# 3. Copy-paste contents of schema-setup.sql
# 4. Run All
```

**Expected Output:**
```
Database MILLIONX created
Schema RAW_DATA created
Table SOCIAL_POSTS created
Table MARKET_ORDERS created
Table PRICE_HISTORY created
Table WEATHER_LOGS created
15 indexes created
8 views created
```

### 1.3 Deployment Option A: Kafka Connect (Recommended)

#### Configure Kafka Connect

```bash
cd millionx-phase2/kafka-connect

# Edit snowflake-sink-social.json
# Update these fields:
# - snowflake.url.name: Your account URL
# - snowflake.user.name: Your username
# - snowflake.private.key: Your private key (see below)
# - snowflake.database.name: MILLIONX
# - snowflake.schema.name: RAW_DATA
```

#### Generate Private Key for Authentication

```bash
# Generate private key
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Copy public key content
cat rsa_key.pub

# In Snowflake, assign public key to user:
ALTER USER <username> SET RSA_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0BAQEF...';
```

#### Deploy Connectors

```bash
# Deploy social posts connector
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @snowflake-sink-social.json

# Deploy market orders connector
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @snowflake-sink-market.json

# Verify connectors are running
curl http://localhost:8083/connectors
curl http://localhost:8083/connectors/snowflake-sink-social/status
curl http://localhost:8083/connectors/snowflake-sink-market/status
```

**Expected Status:**
```json
{
  "name": "snowflake-sink-social",
  "connector": {
    "state": "RUNNING",
    "worker_id": "connect:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "connect:8083"
    }
  ]
}
```

### 1.4 Deployment Option B: Pandas Batch Loader (Alternative)

Use this if Kafka Connect is not available or you prefer more control.

#### Setup Environment

```bash
cd millionx-phase2/snowflake

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env

# Required variables:
SNOWFLAKE_ACCOUNT=<account>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<password>
SNOWFLAKE_DATABASE=MILLIONX
SNOWFLAKE_SCHEMA=RAW_DATA
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
BATCH_SIZE=1000
FLUSH_INTERVAL_SECONDS=60
```

#### Run Batch Loader

```bash
# Run directly
python snowflake_batch_sink.py

# Or using Docker
docker build -t millionx/snowflake-batch-sink .
docker run -d \
  --name snowflake-sink \
  --env-file .env \
  --network millionx-network \
  millionx/snowflake-batch-sink
```

#### Deploy as Kubernetes Job (Production)

```bash
# Create secret with Snowflake credentials
kubectl create secret generic snowflake-credentials \
  --from-literal=account=<account> \
  --from-literal=user=<username> \
  --from-literal=password=<password>

# Deploy as Deployment (continuous)
kubectl apply -f k8s-deployment.yaml
```

---

## 2. Weaviate Deployment

### 2.1 Verify Weaviate is Running

```bash
# Check if Weaviate is accessible
curl http://localhost:8080/v1/meta

# Expected: JSON response with version info
```

### 2.2 Initialize Schema

```bash
cd millionx-phase2/weaviate

# Install dependencies
pip install -r requirements.txt

# Run schema setup
python schema-setup.py

# Expected output:
# Connected to Weaviate at http://localhost:8080
# ✓ Created SocialPost collection
# ✓ Created MarketOrder collection
# 
# === Weaviate Schema Verification ===
# Connected to: http://localhost:8080
# Collections found: 2
# 
# ✓ SocialPost
#   Properties: 20
#   Vector Index: hnsw
#   Distance Metric: cosine
#   Max Connections: 64
# 
# ✓ MarketOrder
#   Properties: 27
#   Vector Index: hnsw
#   Distance Metric: cosine
#   Max Connections: 64
# 
# ✓ Schema setup completed successfully!
```

### 2.3 Verify Schema (Optional)

```bash
# Verify only (don't create)
python schema-setup.py --verify-only

# Force recreate (WARNING: deletes existing data)
python schema-setup.py --force-recreate
```

---

## 3. Weather Fetcher Deployment

### 3.1 Get OpenWeatherMap API Key

1. Sign up at https://openweathermap.org/api
2. Generate API key (free tier: 60 calls/min, 1M calls/month)
3. Wait 10 minutes for API key activation

### 3.2 Deploy as CronJob (Kubernetes)

```bash
cd millionx-phase2/weather-fetcher

# Create secret with API key
kubectl create secret generic weather-fetcher-secrets \
  --from-literal=openweather-api-key=<your_api_key>

# Deploy CronJob
kubectl apply -f k8s-cronjob.yaml

# Verify CronJob
kubectl get cronjobs
kubectl describe cronjob weather-fetcher

# Manually trigger job (for testing)
kubectl create job --from=cronjob/weather-fetcher weather-test-1
kubectl logs job/weather-test-1
```

**Expected Output:**
```
Weather Fetcher Service starting...
Connected to Kafka: kafka:9092
Starting weather fetch for 8 cities...
✓ Fetched weather for Dhaka: Clear, 28.5°C
✓ Published to Kafka: context.weather partition=0 offset=123
✓ Fetched weather for Chittagong: Rain, 26.3°C
✓ Published to Kafka: context.weather partition=0 offset=124
...
=== Weather Fetch Summary ===
Total cities: 8
Successfully fetched: 8
Published to Kafka: 8
Errors: 0
Elapsed time: 9.23s
Weather fetch completed successfully
```

### 3.3 Deploy as Docker Container (Local Testing)

```bash
cd millionx-phase2/weather-fetcher

# Build image
docker build -t millionx/weather-fetcher .

# Run once
docker run --rm \
  -e OPENWEATHER_API_KEY=<your_key> \
  -e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 \
  -e KAFKA_WEATHER_TOPIC=context.weather \
  --network millionx-network \
  millionx/weather-fetcher

# Run on schedule (every hour)
# Add to docker-compose.yml or use cron on host
```

### 3.4 Manual Execution (Development)

```bash
cd millionx-phase2/weather-fetcher

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENWEATHER_API_KEY=<your_key>
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_WEATHER_TOPIC=context.weather

# Run
python weather_fetcher.py
```

---

## 4. Monitoring Deployment

### 4.1 Deploy Prometheus Alert Rules

```bash
cd millionx-phase2/monitoring

# Copy alert rules to Prometheus config directory
# (Adjust path based on your Prometheus setup)
cp prometheus-alerts.yaml /etc/prometheus/alerts/

# Update prometheus.yml to include alerts
# Add to prometheus.yml:
rule_files:
  - '/etc/prometheus/alerts/prometheus-alerts.yaml'

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# OR restart Prometheus container
docker restart prometheus
```

### 4.2 Verify Alerts are Loaded

```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules | jq .

# Check in Prometheus UI
# Navigate to: http://localhost:9090/alerts
# You should see:
# - millionx_phase2_critical (5 rules)
# - millionx_phase2_warning (7 rules)
# - millionx_phase2_info (3 rules)
```

### 4.3 Deploy Alertmanager Configuration

```bash
# Copy alertmanager config
cp alertmanager.yaml /etc/alertmanager/

# Update with your credentials:
# - SMTP settings for email
# - Slack webhook URL
# - Email addresses

# Reload Alertmanager
curl -X POST http://localhost:9093/-/reload

# OR restart container
docker restart alertmanager
```

### 4.4 Test Alert Notifications

```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "component": "test"
    },
    "annotations": {
      "summary": "Test alert from deployment",
      "description": "If you receive this, alerting is working!"
    }
  }]'

# Check if email/Slack notification arrives
```

### 4.5 Import Grafana Dashboards

#### Via UI:

1. Navigate to http://localhost:3000
2. Login (default: admin/admin)
3. Go to **Dashboards** → **Import**
4. Upload `grafana-dashboard-overview.json`
5. Select Prometheus datasource
6. Click **Import**
7. Repeat for `grafana-dashboard-data-quality.json`

#### Via API:

```bash
cd millionx-phase2/monitoring

# Get API key from Grafana
# Settings → API Keys → Add API key

GRAFANA_API_KEY=<your_key>

# Import overview dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @grafana-dashboard-overview.json

# Import data quality dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @grafana-dashboard-data-quality.json
```

#### Via Provisioning (Recommended for Production):

```bash
# Copy dashboards to Grafana provisioning directory
cp grafana-dashboard-*.json /var/lib/grafana/dashboards/

# Create provisioning config
cat > /etc/grafana/provisioning/dashboards/millionx.yaml <<EOF
apiVersion: 1
providers:
  - name: 'MillionX'
    orgId: 1
    folder: 'Phase 2'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
EOF

# Restart Grafana
docker restart grafana
```

---

## 5. Validation & Testing

### 5.1 End-to-End Data Flow Test

```bash
# 1. Check Kafka topics have data
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic sink.snowflake.social \
  --from-beginning \
  --max-messages 5

# 2. Verify data in Snowflake
snowsql -a <account> -u <username> -d MILLIONX -s RAW_DATA -q "
SELECT COUNT(*) as total_posts,
       platform,
       DATE(ingestion_time) as ingestion_date
FROM SOCIAL_POSTS
GROUP BY platform, ingestion_date
ORDER BY ingestion_date DESC
LIMIT 10;
"

# 3. Check Weaviate has embeddings
curl http://localhost:8080/v1/objects?class=SocialPost&limit=5 | jq .

# 4. Verify weather data is flowing
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic context.weather \
  --from-beginning \
  --max-messages 1

# 5. Check Grafana dashboards show data
# Open: http://localhost:3000/d/millionx-overview
```

### 5.2 Monitoring Validation

```bash
# Check Prometheus is scraping metrics
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Verify alert rules are active
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'

# Check for any firing alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state == "firing")'
```

### 5.3 Performance Validation

```bash
# Snowflake query performance
snowsql -q "
SELECT * FROM MILLIONX.RAW_DATA.VW_DAILY_INGESTION_STATS
WHERE ingestion_date = CURRENT_DATE();
"

# Check Snowflake cost
snowsql -q "
SELECT SUM(credits_used) * 2.5 as estimated_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP());
"

# Weaviate query latency
curl -X POST http://localhost:8080/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      Get {
        SocialPost(limit: 10) {
          postId
          platform
          productCategory
        }
      }
    }"
  }' -w "\nTime: %{time_total}s\n"
```

---

## 6. Troubleshooting

### 6.1 Snowflake Issues

#### Connector not starting
```bash
# Check connector logs
curl http://localhost:8083/connectors/snowflake-sink-social/status

# Common issues:
# 1. Invalid credentials → Check private key matches public key in Snowflake
# 2. Network connectivity → Check firewall rules
# 3. Invalid table → Verify schema-setup.sql ran successfully

# View detailed logs
docker logs kafka-connect
```

#### No data in Snowflake tables
```bash
# Check Kafka topics have data
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic sink.snowflake.social \
  --from-beginning \
  --max-messages 1

# Check Snowflake warehouse is running
snowsql -q "SHOW WAREHOUSES;"

# Check for errors in Snowflake
snowsql -q "
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME=>'SOCIAL_POSTS',
  START_TIME=>DATEADD(hours, -1, CURRENT_TIMESTAMP())
));
"
```

### 6.2 Weaviate Issues

#### Schema creation fails
```bash
# Check Weaviate is accessible
curl http://localhost:8080/v1/.well-known/ready

# Delete and recreate schema
python schema-setup.py --force-recreate

# Check Weaviate logs
docker logs weaviate
```

#### No embeddings in Weaviate
```bash
# Verify embedding service is running
docker ps | grep embedding-service

# Check embedding service logs
docker logs embedding-service

# Verify Kafka topic has embeddings
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic processed.validated \
  --from-beginning \
  --max-messages 1 | jq '.embedding'
```

### 6.3 Weather Fetcher Issues

#### API key not working
```bash
# Test API key directly
curl "https://api.openweathermap.org/data/2.5/weather?lat=23.8103&lon=90.4125&appid=<your_key>"

# Common issues:
# 1. API key not activated (wait 10 minutes after creation)
# 2. Rate limit exceeded (60 calls/min on free tier)
# 3. Invalid API key format
```

#### CronJob not running
```bash
# Check CronJob status
kubectl get cronjobs
kubectl describe cronjob weather-fetcher

# Check last job execution
kubectl get jobs
kubectl logs job/<job-name>

# Manually trigger for testing
kubectl create job --from=cronjob/weather-fetcher test-weather-1
```

### 6.4 Monitoring Issues

#### Alerts not firing
```bash
# Check Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets

# Verify alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Check alertmanager is receiving alerts
curl http://localhost:9093/api/v1/alerts

# Test alert manually
curl -X POST http://localhost:9093/api/v1/alerts -d '[{"labels": {"alertname": "test"}}]'
```

#### Grafana dashboards not showing data
```bash
# Test Prometheus datasource in Grafana
# Settings → Data Sources → Prometheus → Test

# Check if metrics exist in Prometheus
curl http://localhost:9090/api/v1/label/__name__/values | jq .

# Verify time range in dashboard (try "Last 6 hours")
```

---

## 📊 Success Metrics

After deployment, you should see:

1. **Snowflake**:
   - ✅ Tables receiving data every minute
   - ✅ Daily cost: $5-15 (with batching)
   - ✅ Query performance: <1s for aggregations

2. **Weaviate**:
   - ✅ ~10-50 objects/sec ingestion rate
   - ✅ Query latency: <100ms for vector search
   - ✅ 99%+ embeddings coverage

3. **Weather Fetcher**:
   - ✅ Runs every hour successfully
   - ✅ 8 cities data published to Kafka
   - ✅ 0 errors, ~9s execution time

4. **Monitoring**:
   - ✅ 2 Grafana dashboards operational
   - ✅ 15 alert rules loaded
   - ✅ Alert notifications working

---

## 🚀 Next Steps

1. **Week 5**: Deploy to production Kubernetes cluster
2. **Phase 3**: Train and deploy ML models
3. **Optimization**: Fine-tune Snowflake warehouse sizes
4. **Security**: Implement secrets management (Vault/AWS Secrets Manager)

---

## 📚 Additional Resources

- [Snowflake Connector for Kafka](https://docs.snowflake.com/en/user-guide/kafka-connector)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [OpenWeatherMap API Docs](https://openweathermap.org/api)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
