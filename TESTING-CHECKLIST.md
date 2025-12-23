# Testing Checklist - Start Here! ✅

## 🎯 Goal

Get the system running and verify it works with mock data (NO paid APIs needed)

**Time Required:** 30 minutes  
**Cost:** $0 (everything runs locally)

---

## ✅ Pre-Flight Checklist

### Required Software

- [ ] Docker Desktop installed and running
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] PowerShell/Terminal access

### Verify Docker:

```powershell
docker --version
docker ps
# Should show Docker is running
```

---

## 🚀 Phase 1: COD Shield (5 minutes)

### Step 1: Start Phase 1 Services

```powershell
cd g:\MillionX-mvp
docker-compose up -d
```

### Step 2: Verify Services Running

```powershell
docker ps
# Should see 3 containers:
# - millionx-redis
# - millionx-fastapi
# - millionx-whatsapp-bot
```

### Step 3: Test FastAPI Risk Engine

```powershell
# Open browser and visit:
http://localhost:8000/docs

# Or test with curl:
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Step 4: Test Risk Score Endpoint

```powershell
# Using PowerShell:
$body = @{
    order_id = "TEST-001"
    customer_phone = "+8801712345678"
    order_amount = 5000
    customer_city = "Dhaka"
    is_first_order = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/risk-score" -Method Post -Body $body -ContentType "application/json"

# Expected Response:
# risk_score: 30 (first order penalty)
# risk_level: "low"
# should_block: false
```

✅ **Phase 1 Working!** If you see risk scores, proceed to Phase 2.

---

## 🌊 Phase 2: Data Pipeline (25 minutes)

### Step 1: Start Kafka Infrastructure (5 min)

```powershell
cd g:\MillionX-mvp\millionx-phase2

# Start all services
docker-compose -f docker-compose.kafka.yml up -d

# Wait 30 seconds for Kafka to initialize
Start-Sleep -Seconds 30
```

### Step 2: Verify Kafka Services (2 min)

```powershell
# Check containers
docker ps | Select-String "millionx"

# Should see 7 containers:
# - millionx-kafka
# - millionx-zookeeper
# - millionx-kafka-ui
# - millionx-kafka-connect
# - millionx-prometheus
# - millionx-grafana
# - millionx-weaviate
```

### Step 3: Create Kafka Topics (2 min)

```powershell
# Option A: Use the script (if bash available)
bash kafka-topics.sh

# Option B: Create manually (PowerShell)
docker exec millionx-kafka kafka-topics --create --topic source.social.tiktok --bootstrap-server localhost:9092 --partitions 6 --replication-factor 1
docker exec millionx-kafka kafka-topics --create --topic source.social.facebook --bootstrap-server localhost:9092 --partitions 6 --replication-factor 1
docker exec millionx-kafka kafka-topics --create --topic source.market.shopify --bootstrap-server localhost:9092 --partitions 4 --replication-factor 1
docker exec millionx-kafka kafka-topics --create --topic source.market.daraz --bootstrap-server localhost:9092 --partitions 4 --replication-factor 1
docker exec millionx-kafka kafka-topics --create --topic context.weather --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1

# Verify topics created
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Step 4: Access Kafka UI (1 min)

```powershell
# Open browser:
http://localhost:8080

# You should see:
# - Kafka cluster info
# - List of topics
# - Consumer groups
```

✅ **Kafka Running!** Topics are ready to receive data.

---

### Step 5: Send Mock Data (5 min)

```powershell
# Install Python dependencies
pip install kafka-python python-dotenv

# Run mock data generator
python mock_data_generator.py

# Expected Output:
# ✅ Connected to Kafka successfully!
# ✅ Successfully sent 100/100 social posts
# ✅ Successfully sent 50/50 orders
# ✅ Successfully sent 8/8 weather records
```

### Step 6: Verify Data in Kafka UI (3 min)

```powershell
# Open: http://localhost:8080

# Click on Topics → source.social.tiktok
# You should see ~50-60 messages

# Click on Topics → source.market.shopify
# You should see ~25-30 messages

# Click "Messages" tab to view actual data
```

✅ **Data Flowing!** Messages are in Kafka.

---

### Step 7: Optional - Start Stream Processors (7 min)

If you want to see data processing in action:

```powershell
# Install Python dependencies for stream processors
cd stream-processors
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env

# Start Privacy Shield
faust -A privacy_shield worker -l info

# In another terminal, start Context Enricher
faust -A context_enricher worker -l info

# In another terminal, start Embedding Service
faust -A embedding_service worker -l info
```

**Note:** This is optional for testing. Stream processors will consume messages from Kafka and process them.

---

## 📊 Verification Checklist

### Phase 1 (COD Shield):

- [ ] Redis container running
- [ ] FastAPI container running (port 8000)
- [ ] WhatsApp bot container running (port 3000)
- [ ] Health endpoint returns success
- [ ] Risk score endpoint returns valid scores

### Phase 2 (Data Pipeline):

- [ ] Kafka container running
- [ ] Zookeeper container running
- [ ] Kafka UI accessible (port 8080)
- [ ] Topics created (visible in UI)
- [ ] Mock data sent successfully
- [ ] Messages visible in Kafka UI

---

## 🎉 Success Indicators

If you see all of these, YOU'RE DONE! ✅

1. **Kafka UI** shows messages in topics
2. **Mock data generator** shows success messages
3. **Docker ps** shows all containers running
4. **No error messages** in docker-compose logs

---

## 🐛 Troubleshooting

### Issue: "Port already in use"

```powershell
# Find process using port
netstat -ano | findstr :8080

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Issue: "Cannot connect to Kafka"

```powershell
# Check if Kafka is ready
docker logs millionx-kafka --tail 50

# Wait 30 more seconds and retry
Start-Sleep -Seconds 30
```

### Issue: "Topics already exist" error

```powershell
# This is OK! Topics are already created
# Just proceed to next step
```

### Issue: Mock data generator fails

```powershell
# Check Kafka is running
docker ps | Select-String "kafka"

# Check topics exist
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092

# Try again
python mock_data_generator.py
```

### Issue: Docker containers keep restarting

```powershell
# Check logs
docker-compose logs <service-name>

# Common fix: Increase Docker memory
# Docker Desktop → Settings → Resources → Memory: 4GB+
```

---

## 🔄 Reset Everything (If Needed)

```powershell
# Stop all containers
docker-compose down
cd millionx-phase2
docker-compose -f docker-compose.kafka.yml down

# Remove volumes (CAUTION: Deletes all data)
docker volume prune -f

# Restart from scratch
docker-compose up -d
docker-compose -f docker-compose.kafka.yml up -d
```

---

## 📚 What to Explore Next

### 1. Kafka UI (http://localhost:8080)

- View topics and partitions
- See messages in real-time
- Monitor consumer lag

### 2. Grafana (http://localhost:3001)

- Login: admin / admin123
- View Kafka metrics dashboard
- See throughput and latency graphs

### 3. FastAPI Docs (http://localhost:8000/docs)

- Interactive API documentation
- Test all endpoints
- View request/response schemas

### 4. Generate More Data

```powershell
# Run generator multiple times to simulate load
python mock_data_generator.py
python mock_data_generator.py
python mock_data_generator.py
```

### 5. Query Data

```powershell
# Consume messages from Kafka (see raw data)
docker exec millionx-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic source.social.tiktok \
  --from-beginning \
  --max-messages 10
```

---

## 💡 Understanding the Data Flow

1. **Mock Data Generator** creates fake posts/orders
2. **Kafka** receives and stores messages in topics
3. **Kafka UI** lets you view the messages
4. **Stream Processors** (if started) process the data
5. **Snowflake/Weaviate** (if configured) store final data

**For now:** You've successfully tested Steps 1-3! 🎉

---

## ✨ Next Steps

**You've completed the basic testing!** Here's what to do next:

### Option A: Deep Dive into Code

- Read [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md)
- Explore [PIPELINE-FLOW-VISUALIZATION.md](PIPELINE-FLOW-VISUALIZATION.md)
- Study the code in `stream-processors/`

### Option B: Configure Real Services (Optional)

- Get free Snowflake trial
- Get free OpenWeather API key
- Connect real storage (Week 4 features)

### Option C: Customize & Extend

- Modify mock data templates
- Add new product categories
- Create custom analytics queries

---

## 📞 Quick Reference

| Service    | URL                        | Credentials      |
| ---------- | -------------------------- | ---------------- |
| FastAPI    | http://localhost:8000/docs | None             |
| Kafka UI   | http://localhost:8080      | None             |
| Grafana    | http://localhost:3001      | admin / admin123 |
| Prometheus | http://localhost:9090      | None             |
| Weaviate   | http://localhost:8082      | None             |

---

**Congratulations!** 🎉 You've successfully tested the MillionX pipeline with mock data!
