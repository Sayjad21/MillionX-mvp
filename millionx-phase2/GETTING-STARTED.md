# Phase 2 Implementation - Getting Started

## ✅ What We've Created

### Project Structure
```
millionx-phase2/
├── docker-compose.kafka.yml     ✅ Kafka stack configuration
├── prometheus.yml               ✅ Monitoring configuration
├── kafka-topics.sh              ✅ Topic creation script
├── kafka-connect-snowflake.json ✅ Snowflake connector config
├── README.md                    ✅ Complete documentation
└── directories for scrapers, processors, k8s
```

### Services Configured
- ✅ **Kafka** - Message streaming backbone
- ✅ **Zookeeper** - Kafka coordination
- ✅ **Kafka UI** - Visual management interface
- ✅ **Kafka Connect** - Snowflake integration ready
- ✅ **Prometheus** - Metrics collection
- ✅ **Grafana** - Monitoring dashboards
- ✅ **Weaviate** - Vector database

---

## 🚀 Next Steps to Start

### Step 1: Start Docker Desktop ⚠️ REQUIRED
Docker Desktop is not currently running. Please:

1. **Launch Docker Desktop**
   - Press Windows key
   - Type "Docker Desktop"
   - Wait for Docker to fully start (whale icon in system tray)

2. **Verify Docker is Running**
   ```powershell
   docker ps
   ```
   You should see a list of running containers (or empty list if none running)

---

### Step 2: Start the Kafka Infrastructure

Once Docker is running, execute these commands in PowerShell:

```powershell
# Navigate to Phase 2 directory
cd C:\Users\Legion\OneDrive\Desktop\millionx\millionx-mvp\millionx-phase2

# Start all services (this will download images on first run)
docker-compose -f docker-compose.kafka.yml up -d

# Wait 30-60 seconds for services to initialize

# Check that all containers are running
docker ps | Select-String "millionx"
```

Expected output: You should see 7 containers running:
- millionx-zookeeper
- millionx-kafka
- millionx-kafka-ui
- millionx-kafka-connect
- millionx-prometheus
- millionx-grafana
- millionx-weaviate

---

### Step 3: Create Kafka Topics

```powershell
# Give Kafka 30 seconds to fully initialize
Start-Sleep -Seconds 30

# Create all topics using the script
bash kafka-topics.sh

# If Git Bash is not installed, create topics manually:
docker exec millionx-kafka kafka-topics --create --topic source.social.tiktok --partitions 6 --replication-factor 1 --bootstrap-server localhost:9092

# Verify topics were created
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092
```

Expected output:
```
_connect-configs
_connect-offsets
_connect-status
context.weather
dead-letters-market
dead-letters-social
enriched.weaviate.vectors
sink.snowflake.orders
sink.weaviate.vectors
source.market.daraz
source.market.shopify
source.social.facebook
source.social.tiktok
```

---

### Step 4: Access the Services

Open these URLs in your browser:

1. **Kafka UI** (Main Interface)
   - URL: http://localhost:8080
   - What to check: Topics list, cluster health

2. **Grafana** (Monitoring)
   - URL: http://localhost:3001
   - Username: `admin`
   - Password: `admin123`

3. **Prometheus** (Metrics)
   - URL: http://localhost:9090
   - Query to try: `kafka_server_BrokerTopicMetrics_Count`

4. **Kafka Connect API**
   - URL: http://localhost:8083/connectors
   - Should return: `[]` (empty array - no connectors yet)

5. **Weaviate**
   - URL: http://localhost:8082/v1/schema
   - Should return: `{"classes":[]}` (empty - schema not created yet)

---

### Step 5: Test Kafka is Working

#### Test 1: Send a Test Message
```powershell
# Send a test message to a topic
echo '{"test":"message","timestamp":"2025-12-20T00:00:00Z"}' | docker exec -i millionx-kafka kafka-console-producer --bootstrap-server localhost:9092 --topic source.social.tiktok
```

#### Test 2: Read the Message Back
```powershell
# Consume messages from the topic (Ctrl+C to stop)
docker exec millionx-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic source.social.tiktok --from-beginning
```

You should see your test message printed!

---

## 📊 Current Status

### Week 1 Progress: Kafka Infrastructure
- ✅ Project structure created
- ✅ Docker Compose configuration complete
- ✅ Monitoring stack configured (Prometheus + Grafana)
- ✅ Kafka Connect ready for Snowflake integration
- ✅ Weaviate vector database deployed
- ⏳ **NEXT:** Start Docker and launch services
- ⏳ **THEN:** Create topics and validate

### Upcoming Milestones
- **Week 2:** Build scraper agents (TikTok, Facebook, Shopify, Daraz)
- **Week 3:** Implement stream processors (Privacy Shield, Context Enricher, Embeddings)
- **Week 4:** Connect to Snowflake and Weaviate, optimize performance

---

## 🚨 Troubleshooting

### Issue: Docker Desktop won't start
**Solution:**
1. Check Windows Updates are installed
2. Enable WSL 2 if needed: `wsl --install`
3. Restart your computer
4. Try launching Docker Desktop again

### Issue: Port conflicts (8080, 9092, etc.)
**Solution:**
```powershell
# Check what's using the port
netstat -ano | findstr :8080

# Kill the process using the port (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue: Kafka topics creation fails
**Solution:**
```powershell
# Wait longer for Kafka to initialize
Start-Sleep -Seconds 60

# Try creating one topic manually
docker exec millionx-kafka kafka-topics --create --topic test --partitions 1 --replication-factor 1 --bootstrap-server localhost:9092

# Check Kafka logs
docker logs millionx-kafka
```

### Issue: Out of disk space
**Solution:**
```powershell
# Clean up old Docker resources
docker system prune -a --volumes

# This will remove unused images, containers, and volumes
```

---

## 🎯 Success Criteria Checklist

Before moving to Week 2, verify:

- [ ] Docker Desktop is running
- [ ] All 7 containers are up and healthy
- [ ] Kafka UI accessible at http://localhost:8080
- [ ] 10+ Kafka topics created
- [ ] Test message can be produced and consumed
- [ ] Grafana accessible at http://localhost:3001
- [ ] Prometheus showing Kafka metrics
- [ ] No errors in container logs

**Validation Command:**
```powershell
# Check all containers are healthy
docker ps --filter "name=millionx" --format "table {{.Names}}\t{{.Status}}"
```

All should show "Up" status!

---

## 📞 Need Help?

If you encounter issues:

1. **Check container logs:**
   ```powershell
   docker logs millionx-kafka
   docker logs millionx-zookeeper
   docker logs millionx-kafka-connect
   ```

2. **Restart a specific service:**
   ```powershell
   docker-compose -f docker-compose.kafka.yml restart kafka
   ```

3. **Stop everything and start fresh:**
   ```powershell
   docker-compose -f docker-compose.kafka.yml down -v
   docker-compose -f docker-compose.kafka.yml up -d
   ```

---

**Status:** Ready to launch! 🚀  
**Last Updated:** December 20, 2025  
**Next Action:** Start Docker Desktop and run the commands above
