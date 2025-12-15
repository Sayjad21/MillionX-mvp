# MillionX Phase 1 Testing Guide

## 📋 Overview
Complete testing guide for Phase 1 MVP validation. This covers Days 0-3 implementation verification, functional testing, performance benchmarking, and end-to-end system validation.

**Testing Levels:**
- ✅ Unit Tests (FastAPI & WhatsApp Bot)
- ✅ Integration Tests  
- ✅ Performance Benchmarks
- ✅ End-to-End System Tests
- ✅ Manual Acceptance Tests

---

## 🚀 Pre-Testing Setup

### 1. Environment Verification

#### Check All Services Are Running
```bash
# Using Docker (Recommended)
cd millionx-mvp
docker-compose ps

# Expected output:
# NAME                   STATUS    PORTS
# millionx-fastapi       healthy   0.0.0.0:8000->8000/tcp
# millionx-whatsapp-bot  healthy   0.0.0.0:3000->3000/tcp
# millionx-redis         healthy   0.0.0.0:6379->6379/tcp
```

#### Verify Health Endpoints
```bash
# FastAPI Health
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"COD Shield","redis_connected":true}

# WhatsApp Bot Health
curl http://localhost:3000/
# Expected: {"service":"Bhai-Bot WhatsApp Interface",...}

# Redis Health
docker exec millionx-redis redis-cli ping
# Expected: PONG
```

### 2. Database Setup (Supabase)

#### Run Schema Creation
1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `supabase-schema.sql`
3. Execute the script
4. Verify tables created:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

Expected tables:
- merchants
- orders
- blacklist
- risk_assessments

#### Verify Seed Data
```sql
SELECT 'Merchants' as table_name, COUNT(*) as count FROM merchants
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Blacklist', COUNT(*) FROM blacklist;
```

Expected:
- Merchants: 3
- Orders: 150+
- Blacklist: 5

### 3. Seed Redis Test Data

```bash
cd fastapi-risk-engine
python seed_data.py
```

Expected output:
```
✅ Seeded 3 blacklist entries
```

Verify in Redis:
```bash
docker exec millionx-redis redis-cli
> GET blacklist:+8801799999999
# Expected: "3"
```

---

## 🧪 Unit Testing

### FastAPI Risk Engine Tests

#### Run All Tests
```bash
cd fastapi-risk-engine
pytest tests/ -v --cov --cov-report=html
```

#### Expected Results
```
tests/test_risk_engine.py::TestHealthEndpoint::test_health_check PASSED
tests/test_risk_engine.py::TestLowRiskScenarios::test_regular_customer_small_order PASSED
tests/test_risk_engine.py::TestLowRiskScenarios::test_known_customer_medium_order PASSED
tests/test_risk_engine.py::TestMediumRiskScenarios::test_first_order_high_value PASSED
tests/test_risk_engine.py::TestMediumRiskScenarios::test_first_order_medium_value PASSED
tests/test_risk_engine.py::TestHighRiskScenarios::test_blacklisted_customer PASSED
tests/test_risk_engine.py::TestBlacklistManagement::test_add_to_blacklist PASSED
tests/test_risk_engine.py::TestBlacklistManagement::test_check_blacklist_exists PASSED
tests/test_risk_engine.py::TestBlacklistManagement::test_check_blacklist_not_exists PASSED
tests/test_risk_engine.py::TestPerformance::test_response_time_under_1_second PASSED
tests/test_risk_engine.py::TestValidation::test_missing_required_fields PASSED

====== 11 passed in X.XXs ======
Coverage: >85%
```

#### Troubleshooting
**Issue:** Redis connection error
```bash
# Solution: Ensure Redis is running
docker-compose restart redis
```

**Issue:** Import errors
```bash
# Solution: Activate virtual environment
cd fastapi-risk-engine
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### WhatsApp Bot Tests

#### Run All Tests
```bash
cd whatsapp-bot
npm test
```

#### Expected Results
```
PASS tests/whatsapp.test.js
  WhatsApp Webhook Verification
    ✓ Should verify webhook with correct token
    ✓ Should reject webhook with incorrect token
    ✓ Should reject non-subscribe mode
  Intent Detection and Routing
    ✓ Should detect profit query intent
    ✓ Should detect inventory query intent
    ✓ Should detect risk check intent
    ✓ Should detect fraud report intent
  Message Handling
    ✓ Should handle profit query message
    ✓ Should handle risk check message
    ✓ Should handle unknown message with help text
  Phone Number Extraction
    ✓ Should extract Bangladesh phone number
  Error Handling
    ✓ Should handle FastAPI connection error gracefully
    ✓ Should handle malformed webhook payload
  WhatsApp API Integration
    ✓ Should send message with correct format
  Health Check
    ✓ Should return service info on root endpoint

Test Suites: 1 passed, 1 total
Tests:       15 passed, 15 total
```

---

## 🔗 Integration Testing

### Test 1: FastAPI → Redis Integration

#### Scenario: Add to Blacklist, Then Check Risk
```bash
# Step 1: Add number to blacklist
curl -X POST http://localhost:8000/api/v1/blacklist/add \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+8801755555555",
    "reason": "Test blacklist entry",
    "merchant_id": "MERCH-TEST"
  }'

# Expected: {"status":"added","phone":"+8801755555555"}

# Step 2: Verify in Redis
docker exec millionx-redis redis-cli GET blacklist:+8801755555555
# Expected: "1"

# Step 3: Check risk score
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "TEST-INT-001",
    "merchant_id": "MERCH-TEST",
    "customer_phone": "+8801755555555",
    "delivery_address": {"area": "Gulshan", "city": "Dhaka", "postal_code": "1212"},
    "order_details": {"total_amount": 500, "currency": "BDT", "items_count": 1, "is_first_order": false},
    "timestamp": "2025-12-15T10:00:00Z"
  }'

# Expected: risk_score > 30 (blacklist factor should be present)
```

**Success Criteria:**
- ✅ Blacklist entry added
- ✅ Redis reflects the change
- ✅ Risk score increases for blacklisted number

### Test 2: WhatsApp Bot → FastAPI Integration

#### Scenario: Risk Check via WhatsApp
```bash
# Simulate WhatsApp webhook call
curl -X POST http://localhost:3000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+8801712345678",
            "type": "text",
            "text": {
              "body": "risk check +8801799999999"
            }
          }]
        }
      }]
    }]
  }'

# Check WhatsApp bot logs - should show:
# - ✅ Message received
# - ✅ Intent detected: risk check
# - ✅ FastAPI called
# - ✅ Response formatted
# - ✅ WhatsApp API called (or logged if not configured)
```

**Success Criteria:**
- ✅ WhatsApp webhook accepts message
- ✅ Intent correctly identified
- ✅ FastAPI risk endpoint called
- ✅ Response formatted correctly

### Test 3: Network Effect (Report Fraudster)

#### Scenario: One Merchant Reports, All Benefit
```bash
# Step 1: Merchant A reports fraudster
curl -X POST http://localhost:3000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+8801712345678",
            "type": "text",
            "text": {
              "body": "report +8801766666666"
            }
          }]
        }
      }]
    }]
  }'

# Step 2: Verify blacklist count increased
docker exec millionx-redis redis-cli GET blacklist:+8801766666666
# Expected: count incremented

# Step 3: Merchant B checks same number (different merchant)
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "TEST-NETWORK-001",
    "merchant_id": "MERCH-B",
    "customer_phone": "+8801766666666",
    "delivery_address": {"area": "Dhanmondi", "city": "Dhaka", "postal_code": "1205"},
    "order_details": {"total_amount": 1000, "currency": "BDT", "items_count": 2, "is_first_order": true},
    "timestamp": "2025-12-15T11:00:00Z"
  }'

# Expected: High risk score due to blacklist (even though different merchant)
```

**Success Criteria:**
- ✅ Report increases blacklist count
- ✅ All subsequent risk checks reflect updated blacklist
- ✅ Network effect demonstrated (one report protects all)

---

## ⚡ Performance Benchmarking

### Run Benchmark Script
```bash
cd millionx-mvp/tests
python benchmark.py
```

### Expected Output
```
========================================================================
🚀 COD SHIELD API PERFORMANCE BENCHMARK
========================================================================

========================================================================
🏥 HEALTH CHECK
========================================================================
✅ API is healthy: {'status': 'healthy', 'service': 'COD Shield'}

========================================================================
🔄 SEQUENTIAL BENCHMARK (100 requests per scenario)
========================================================================

Testing LOW_RISK scenario...
  Progress: 100/100 requests

📊 Results for LOW_RISK:
  Success Rate: 100.0% (100/100)
  
  Response Times (including network):
    Average:   45.32 ms
    Median:    43.21 ms
    P95:       67.89 ms ✅
    P99:       89.45 ms
    Min:       32.10 ms
    Max:       98.76 ms
  
  API Processing Times:
    Average:   38.45 ms ✅
  
  Risk Assessment:
    Avg Score: 15.3/100

========================================================================
⚡ CONCURRENT BENCHMARK (100 requests, 10 workers)
========================================================================
[Similar output for concurrent tests]

========================================================================
📈 BENCHMARK SUMMARY
========================================================================

✅ Performance Targets:
   - P95 Response Time < 100ms
   - API Processing Time < 100ms
   - Success Rate > 99%

✅ Check results above to verify all targets are met!
```

### Performance Acceptance Criteria
- ✅ P95 response time < 100ms
- ✅ Average API processing < 50ms
- ✅ Success rate > 99%
- ✅ No timeout errors
- ✅ Concurrent requests handled successfully

### Troubleshooting Performance Issues
**Issue:** P95 > 100ms
- Check Redis connection latency
- Verify no CPU throttling in Docker
- Ensure local network is not congested

**Issue:** High failure rate
- Check API logs for errors
- Verify Redis is not overloaded
- Increase Redis memory if needed

---

## 🌐 End-to-End System Tests

### Test Scenario 1: Low Risk Order Flow

#### Objective: Verify complete flow for safe order

**Step 1:** Submit order to risk API
```bash
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "E2E-LOW-001",
    "merchant_id": "MERCH-E2E",
    "customer_phone": "+8801700000000",
    "delivery_address": {"area": "Gulshan", "city": "Dhaka", "postal_code": "1212"},
    "order_details": {"total_amount": 450, "currency": "BDT", "items_count": 1, "is_first_order": false},
    "timestamp": "2025-12-15T10:00:00Z"
  }'
```

**Expected Response:**
```json
{
  "order_id": "E2E-LOW-001",
  "risk_score": 15,
  "risk_level": "LOW",
  "recommendation": "PROCEED_WITH_COD",
  "factors": [],
  "suggested_actions": ["Process order normally"],
  "processing_time_ms": 45
}
```

**Validation:**
- ✅ Risk score 0-40
- ✅ Risk level: LOW
- ✅ Recommendation: PROCEED_WITH_COD
- ✅ Response time < 100ms

---

### Test Scenario 2: High Risk Order Flow

#### Objective: Verify blacklist detection and recommendation

**Step 1:** Submit high-risk order
```bash
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "E2E-HIGH-001",
    "merchant_id": "MERCH-E2E",
    "customer_phone": "+8801799999999",
    "delivery_address": {"area": "Unknown", "city": "Dhaka", "postal_code": ""},
    "order_details": {"total_amount": 2500, "currency": "BDT", "items_count": 5, "is_first_order": true},
    "timestamp": "2025-12-15T10:00:00Z"
  }'
```

**Expected Response:**
```json
{
  "order_id": "E2E-HIGH-001",
  "risk_score": 85,
  "risk_level": "HIGH",
  "recommendation": "ADVANCE_PAYMENT_REQUIRED",
  "factors": [
    {
      "factor": "BLACKLISTED_PHONE",
      "weight": 60,
      "description": "Phone has 3 previous failed deliveries"
    },
    {
      "factor": "HIGH_VALUE_FIRST_ORDER",
      "weight": 30,
      "description": "Order amount Tk 2500 for new customer"
    }
  ],
  "suggested_actions": [
    "Request 50% advance via bKash",
    "Limit COD to Tk 500"
  ],
  "processing_time_ms": 52
}
```

**Validation:**
- ✅ Risk score 71-100
- ✅ Risk level: HIGH
- ✅ Blacklist factor present (60 points)
- ✅ High value first order factor present (30 points)
- ✅ Recommendation: ADVANCE_PAYMENT_REQUIRED

---

### Test Scenario 3: WhatsApp Complete Flow

#### Objective: Test full merchant interaction via WhatsApp

**Step 1:** Profit Query
```bash
curl -X POST http://localhost:3000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+8801712345678",
            "type": "text",
            "text": {"body": "ei mashe labh koto?"}
          }]
        }
      }]
    }]
  }'
```

**Expected:** Profit summary response in logs

**Step 2:** Risk Check
```bash
curl -X POST http://localhost:3000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+8801712345678",
            "type": "text",
            "text": {"body": "risk check +8801799999999"}
          }]
        }
      }]
    }]
  }'
```

**Expected:** Risk assessment response with high risk warning

**Step 3:** Report Fraudster
```bash
curl -X POST http://localhost:3000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "+8801712345678",
            "type": "text",
            "text": {"body": "report +8801799999999"}
          }]
        }
      }]
    }]
  }'
```

**Expected:** Confirmation message with network effect

**Validation:**
- ✅ All intents correctly detected
- ✅ FastAPI called for risk check
- ✅ Blacklist updated for report
- ✅ Responses formatted correctly

---

## ✅ Manual Acceptance Testing

### Checklist: Core Functionality

#### Day 0: Environment
- [ ] Project structure exists (fastapi-risk-engine, whatsapp-bot, tests)
- [ ] Git repository initialized
- [ ] .gitignore excludes .env files
- [ ] Supabase project created and accessible
- [ ] Redis container running
- [ ] WhatsApp Business API credentials obtained
- [ ] .env file configured with all credentials

#### Day 1: FastAPI Risk Engine
- [ ] FastAPI server starts without errors
- [ ] Swagger docs accessible at http://localhost:8000/docs
- [ ] Health endpoint returns healthy status
- [ ] Risk score endpoint accepts valid requests
- [ ] Risk calculation includes 4 factors (blacklist, first order, address, time)
- [ ] Blacklist add endpoint works
- [ ] Blacklist check endpoint works
- [ ] Redis integration functional
- [ ] Response times < 100ms
- [ ] Unit tests pass (>85% coverage)

#### Day 2: WhatsApp Bot
- [ ] Node.js server starts without errors
- [ ] Webhook verification endpoint works
- [ ] Webhook POST handler accepts messages
- [ ] Profit query intent detected
- [ ] Inventory query intent detected
- [ ] Risk check intent detected
- [ ] Report fraudster intent detected
- [ ] Phone number extraction works
- [ ] FastAPI integration works
- [ ] Help message displays correctly
- [ ] Jest tests pass

#### Day 3: Docker & Testing
- [ ] Dockerfile for FastAPI builds successfully
- [ ] Dockerfile for WhatsApp bot builds successfully
- [ ] docker-compose.yml validated
- [ ] All containers start via docker-compose up
- [ ] Health checks pass for all services
- [ ] FastAPI unit tests comprehensive
- [ ] WhatsApp bot unit tests comprehensive
- [ ] Performance benchmark script created
- [ ] Benchmark shows P95 < 100ms
- [ ] Demo script prepared

#### Database & Persistence
- [ ] Supabase tables created (merchants, orders, blacklist, risk_assessments)
- [ ] Seed data inserted successfully
- [ ] Indexes created for performance
- [ ] Can query tables via Supabase dashboard
- [ ] Redis data persists across restarts

---

## 🐛 Troubleshooting Common Issues

### Issue: FastAPI Returns 500 Error
**Symptoms:** Internal server error on risk score endpoint

**Diagnosis:**
```bash
# Check FastAPI logs
docker-compose logs fastapi
```

**Solutions:**
- Verify Redis is running: `docker-compose ps redis`
- Check .env file has REDIS_HOST=redis (for Docker)
- Restart services: `docker-compose restart`

### Issue: WhatsApp Bot Can't Connect to FastAPI
**Symptoms:** Risk check returns error message

**Diagnosis:**
```bash
# Check WhatsApp bot logs
docker-compose logs whatsapp-bot

# Check if FastAPI is accessible from bot container
docker-compose exec whatsapp-bot wget -O- http://fastapi:8000/health
```

**Solutions:**
- Verify FASTAPI_URL=http://fastapi:8000 in docker-compose.yml
- Ensure both services on same network
- Restart: `docker-compose restart whatsapp-bot`

### Issue: Tests Fail with Import Errors
**Symptoms:** ModuleNotFoundError in pytest

**Solutions:**
```bash
# FastAPI tests
cd fastapi-risk-engine
pip install -r requirements.txt
pytest tests/ -v

# WhatsApp bot tests
cd whatsapp-bot
npm install
npm test
```

### Issue: Performance Benchmark Fails
**Symptoms:** Connection refused or timeouts

**Solutions:**
- Ensure API is running: `curl http://localhost:8000/health`
- Check if port 8000 is available: `netstat -an | findstr 8000`
- Reduce concurrent workers: Edit `benchmark.py`, change workers=10 to workers=5

---

## 📊 Success Metrics

### Phase 1 Completion Criteria

| Metric | Target | Test Method |
|--------|--------|-------------|
| API Response Time (P95) | <100ms | Performance benchmark |
| Test Coverage | >85% | pytest --cov, jest --coverage |
| Success Rate | >99% | Integration tests, benchmark |
| Risk Score Accuracy | >90% | Manual validation of scenarios |
| Uptime | 100% during testing | Health checks, docker ps |
| Blacklist Detection | 100% | Integration test scenario 1 |
| Network Effect | Works | Integration test scenario 3 |

### Final Validation Checklist
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Performance benchmarks meet targets
- [ ] E2E scenarios validated
- [ ] Manual acceptance tests complete
- [ ] Docker deployment working
- [ ] Demo rehearsed successfully

---

## 🎓 Testing Best Practices

### Before Each Test Session
1. ✅ Pull latest code: `git pull`
2. ✅ Rebuild containers: `docker-compose build`
3. ✅ Start fresh: `docker-compose down && docker-compose up -d`
4. ✅ Wait for health checks: `docker-compose ps` (all healthy)
5. ✅ Seed test data: `python seed_data.py`

### During Testing
- 📝 Log all issues with reproduction steps
- 📊 Take screenshots of errors
- ⏱️ Note performance degradation
- 🔄 Test on clean state (restart services between tests)

### After Testing
- ✅ Update test documentation
- ✅ File bugs for failures
- ✅ Update metrics dashboard
- ✅ Share results with team

---

## 📝 Test Report Template

```markdown
# Phase 1 Test Report - [Date]

## Summary
- **Tester:** [Name]
- **Duration:** [X hours]
- **Environment:** [Docker/Local/Cloud]

## Results
- ✅ Unit Tests: [X/X passed]
- ✅ Integration Tests: [X/X passed]
- ⚠️ Performance: P95 = [X]ms (Target: <100ms)
- ✅ E2E Tests: [X/X scenarios passed]

## Issues Found
1. [Issue description]
   - Severity: [High/Medium/Low]
   - Reproduction steps: [...]
   - Status: [Open/Fixed]

## Recommendations
- [Recommendation 1]
- [Recommendation 2]

## Sign-off
Phase 1 is [READY/NOT READY] for demo.
```

---

**Testing completed successfully = Phase 1 DONE! 🎉**

**Next Steps:**
- Review test results with team
- Fix any critical issues
- Rehearse demo 3x
- Deploy to production environment
- Schedule customer pilots
