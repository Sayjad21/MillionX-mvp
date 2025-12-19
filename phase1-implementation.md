# Phase 1: Foundation & COD Shield MVP - Implementation Plan

## Executive Summary
This document outlines the complete implementation strategy for Phase 1 of the Commerce Intelligence Platform. The goal is to build a production-ready MVP featuring the **COD Shield** (fraud detection) and basic **Bhai-Bot** (WhatsApp integration) within a hackathon-sprint timeline.

---

## 1. System Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  WhatsApp User  │◄───────►│   Webhook API    │◄───────►│   Bhai-Bot      │
│  (Merchant)     │  HTTPS  │   (Node.js)      │  Event  │   Router        │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │                            │
                                     ▼                            ▼
                            ┌──────────────────┐         ┌─────────────────┐
                            │  Supabase Auth   │         │  FastAPI Core   │
                            │  & User DB       │         │  (Intelligence) │
                            └──────────────────┘         └─────────────────┘
                                     │                            │
                                     └────────────┬───────────────┘
                                                  ▼
                                         ┌─────────────────┐
                                         │  COD Shield API │
                                         │  /risk-score    │
                                         └─────────────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                           ┌─────────────────┐        ┌─────────────────┐
                           │  PostgreSQL     │        │  Redis Cache    │
                           │  (Orders, Users)│        │  (Blacklists)   │
                           └─────────────────┘        └─────────────────┘
```

---

## 2. Technology Stack (Phase 1 Specific)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Risk Engine | FastAPI | 0.104+ | High-performance ML inference |
| Real-time Events | Node.js + Express | 18.x | WhatsApp webhook handling |
| Database | PostgreSQL (Supabase) | 15.x | Transactional data storage |
| Cache | Redis | 7.x | Blacklist & session cache |
| Messaging | WhatsApp Business API | v18.0 | User interface |
| Container | Docker | 24.x | Deployment packaging |
| Hosting | DigitalOcean/AWS | - | Cloud infrastructure |

---

## 3. Core Components Implementation

### 3.1 COD Shield (Risk Scoring Service)

#### **Purpose**
Prevent COD fraud by scoring order risk in real-time based on:
- Phone number blacklist history
- Order amount vs. customer history
- Delivery address patterns
- Time-based anomalies

#### **API Endpoint**
```
POST /api/v1/risk-score
```

#### **Input Schema**
```json
{
  "order_id": "ORD-12345",
  "merchant_id": "MERCH-789",
  "customer_phone": "+8801712345678",
  "delivery_address": {
    "area": "Dhanmondi",
    "city": "Dhaka",
    "postal_code": "1205"
  },
  "order_details": {
    "total_amount": 1500.00,
    "currency": "BDT",
    "items_count": 2,
    "is_first_order": true
  },
  "timestamp": "2025-12-13T10:30:00Z"
}
```

#### **Output Schema**
```json
{
  "order_id": "ORD-12345",
  "risk_score": 85,
  "risk_level": "HIGH",
  "recommendation": "ADVANCE_PAYMENT_REQUIRED",
  "factors": [
    {
      "factor": "BLACKLISTED_PHONE",
      "weight": 60,
      "description": "Phone number has 2 previous failed deliveries"
    },
    {
      "factor": "HIGH_VALUE_FIRST_ORDER",
      "weight": 25,
      "description": "Order amount > Tk 1000 for new customer"
    }
  ],
  "suggested_actions": [
    "Request 50% advance payment via bKash",
    "Limit COD to Tk 500 maximum"
  ],
  "processing_time_ms": 45
}
```

#### **Risk Score Calculation Logic**
```python
def calculate_risk_score(order_data):
    base_score = 0
    
    # Factor 1: Blacklist Check (0-60 points)
    blacklist_hits = check_redis_blacklist(order_data['customer_phone'])
    if blacklist_hits > 0:
        base_score += min(blacklist_hits * 30, 60)
    
    # Factor 2: First Order + High Value (0-30 points)
    if order_data['order_details']['is_first_order']:
        if order_data['order_details']['total_amount'] > 1000:
            base_score += 30
        elif order_data['order_details']['total_amount'] > 500:
            base_score += 15
    
    # Factor 3: Address Risk (0-20 points)
    risky_areas = ['Unknown', 'Remote']
    if order_data['delivery_address']['area'] in risky_areas:
        base_score += 20
    
    # Factor 4: Time Anomaly (0-10 points)
    if is_suspicious_time(order_data['timestamp']):  # e.g., 2-5 AM orders
        base_score += 10
    
    return min(base_score, 100)
```

#### **Decision Thresholds**
- **0-40**: LOW risk → Proceed with COD
- **41-70**: MEDIUM risk → Require order confirmation call
- **71-100**: HIGH risk → Advance payment mandatory

---

### 3.2 Bhai-Bot (WhatsApp Interface)

#### **Purpose**
Natural language interface for merchants to:
- Check profit/sales metrics
- Receive inventory alerts
- Upload product images for auto-cataloging (Phase 1: basic acknowledgment)

#### **Webhook Endpoint**
```
POST /webhook/whatsapp
```

#### **Input (WhatsApp Message)**
```json
{
  "from": "+8801712345678",
  "timestamp": "1702467000",
  "type": "text",
  "text": {
    "body": "ei mashe labh koto?"
  }
}
```

#### **Output (Response to WhatsApp)**
```json
{
  "to": "+8801712345678",
  "type": "text",
  "text": {
    "body": "📊 December Profit Summary:\n\n💰 Revenue: Tk 45,300\n💸 Costs: Tk 32,100\n✅ Net Profit: Tk 13,200 (+18% vs Nov)\n\nTop seller: Blue T-shirt (45 units)"
  }
}
```

#### **Supported Commands (Phase 1)**

| User Input (Benglish) | Intent | Action |
|----------------------|--------|--------|
| "ei mashe labh koto?" | Check profit | Query orders table, calculate P&L |
| "inventory check" | Stock status | Return low-stock items (<10 units) |
| "risk check [phone]" | Manual risk check | Call COD Shield API |
| **"report [phone]"** | **Report fraudster** | **Add to network blacklist (Network Effect!)** |
| *[Image Upload]* | Product image | Acknowledge + store for future processing |

#### **Rule-Based Router Logic**
```javascript
function routeMessage(message) {
  const text = message.text.body.toLowerCase();
  
  if (text.match(/labh|profit|income/)) {
    return handleProfitQuery(message.from);
  }
  
  if (text.match(/inventory|stock/)) {
    return handleInventoryQuery(message.from);
  }
  
  if (text.match(/risk check/)) {
    const phone = extractPhoneNumber(text);
    return handleRiskCheck(phone);
  }
  
  if (message.type === 'image') {
    return handleImageUpload(message);
  }
  
  return "🤖 Bhai-Bot here! Try:\n- 'labh koto?' (check profit)\n- 'inventory check'\n- 'risk check +8801XXXXXXX'";
}
```

---

### 3.3 Database Schema (PostgreSQL via Supabase)

#### **merchants Table**
```sql
CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    registration_date TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **orders Table**
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID REFERENCES merchants(id),
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_area VARCHAR(100),
    delivery_city VARCHAR(50),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX idx_orders_merchant_id ON orders(merchant_id);
CREATE INDEX idx_orders_risk_score ON orders(risk_score);
```

#### **blacklist Table**
```sql
CREATE TABLE blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    failed_deliveries INTEGER DEFAULT 1,
    total_fraud_amount DECIMAL(10,2),
    last_incident_date TIMESTAMPTZ,
    reason TEXT,
    added_by UUID REFERENCES merchants(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.4 Redis Cache Structure

#### **Blacklist Cache**
```
Key: blacklist:{phone_number}
Value: {
  "hits": 2,
  "last_updated": "2025-12-13T10:30:00Z",
  "severity": "high"
}
TTL: 24 hours
```

#### **Session Cache**
```
Key: session:{merchant_id}
Value: {
  "last_query": "profit",
  "context": {...}
}
TTL: 30 minutes
```

---

## 4. Implementation Steps

### Step 1: Environment Setup (Day 0)
```bash
# Initialize project structure
mkdir millionx-mvp && cd millionx-mvp
mkdir fastapi-risk-engine whatsapp-bot shared

# FastAPI setup
cd fastapi-risk-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn redis supabase pydantic python-dotenv

# Node.js setup
cd ../whatsapp-bot
npm init -y
npm install express axios dotenv redis @supabase/supabase-js
```

### Step 2: FastAPI Risk Engine (Day 1)
```python
# fastapi-risk-engine/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from typing import List, Dict
import os

app = FastAPI(title="COD Shield API")
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class OrderData(BaseModel):
    order_id: str
    merchant_id: str
    customer_phone: str
    delivery_address: Dict
    order_details: Dict
    timestamp: str

class RiskFactor(BaseModel):
    factor: str
    weight: int
    description: str

class RiskResponse(BaseModel):
    order_id: str
    risk_score: int
    risk_level: str
    recommendation: str
    factors: List[RiskFactor]
    suggested_actions: List[str]
    processing_time_ms: int

@app.post("/api/v1/risk-score", response_model=RiskResponse)
async def calculate_risk(order: OrderData):
    import time
    start_time = time.time()
    
    risk_score = 0
    factors = []
    
    # Check blacklist
    blacklist_key = f"blacklist:{order.customer_phone}"
    blacklist_data = redis_client.get(blacklist_key)
    
    if blacklist_data:
        hits = int(blacklist_data)
        weight = min(hits * 30, 60)
        risk_score += weight
        factors.append(RiskFactor(
            factor="BLACKLISTED_PHONE",
            weight=weight,
            description=f"Phone has {hits} previous failed deliveries"
        ))
    
    # First order + high value
    if order.order_details.get('is_first_order'):
        amount = order.order_details.get('total_amount', 0)
        if amount > 1000:
            risk_score += 30
            factors.append(RiskFactor(
                factor="HIGH_VALUE_FIRST_ORDER",
                weight=30,
                description=f"Order amount Tk {amount} for new customer"
            ))
    
    # Determine risk level
    if risk_score <= 40:
        risk_level = "LOW"
        recommendation = "PROCEED_WITH_COD"
        actions = ["Process order normally"]
    elif risk_score <= 70:
        risk_level = "MEDIUM"
        recommendation = "CONFIRMATION_CALL_REQUIRED"
        actions = ["Call customer to confirm", "Verify delivery address"]
    else:
        risk_level = "HIGH"
        recommendation = "ADVANCE_PAYMENT_REQUIRED"
        actions = ["Request 50% advance via bKash", "Limit COD to Tk 500"]
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return RiskResponse(
        order_id=order.order_id,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        factors=factors,
        suggested_actions=actions,
        processing_time_ms=processing_time
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "COD Shield"}
```

### Step 3: WhatsApp Bot (Day 2)
```javascript
// whatsapp-bot/index.js
const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const WHATSAPP_TOKEN = process.env.WHATSAPP_TOKEN;

// Webhook verification
app.get('/webhook/whatsapp', (req, res) => {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];
    
    if (mode === 'subscribe' && token === process.env.VERIFY_TOKEN) {
        res.status(200).send(challenge);
    } else {
        res.sendStatus(403);
    }
});

// Message handler
app.post('/webhook/whatsapp', async (req, res) => {
    try {
        const message = req.body.entry[0].changes[0].value.messages[0];
        const from = message.from;
        const text = message.text?.body?.toLowerCase() || '';
        
        let response = '';
        
        if (text.match(/labh|profit/)) {
            response = await handleProfitQuery(from);
        } else if (text.match(/inventory|stock/)) {
            response = await handleInventoryQuery(from);
        } else if (text.match(/risk check/)) {
            const phone = extractPhoneNumber(text);
            response = await handleRiskCheck(phone);
        } else {
            response = "🤖 Bhai-Bot here!\n\nTry:\n• 'labh koto?' - Check profit\n• 'inventory check' - Stock status\n• 'risk check +880...' - Check order risk";
        }
        
        await sendWhatsAppMessage(from, response);
        res.sendStatus(200);
    } catch (error) {
        console.error('Error:', error);
        res.sendStatus(500);
    }
});

async function handleRiskCheck(phone) {
    try {
        const response = await axios.post(`${FASTAPI_URL}/api/v1/risk-score`, {
            order_id: `MANUAL-${Date.now()}`,
            merchant_id: 'DEMO-MERCHANT',
            customer_phone: phone,
            delivery_address: { area: 'Unknown', city: 'Dhaka', postal_code: '' },
            order_details: { total_amount: 500, currency: 'BDT', items_count: 1, is_first_order: false },
            timestamp: new Date().toISOString()
        });
        
        const data = response.data;
        return `🛡️ Risk Check: ${phone}\n\n` +
               `Risk Score: ${data.risk_score}/100\n` +
               `Level: ${data.risk_level}\n` +
               `Recommendation: ${data.recommendation.replace(/_/g, ' ')}\n\n` +
               `Actions:\n${data.suggested_actions.map(a => `• ${a}`).join('\n')}`;
    } catch (error) {
        return '❌ Risk check failed. Try again.';
    }
}

async function sendWhatsAppMessage(to, text) {
    await axios.post(
        `https://graph.facebook.com/v18.0/${process.env.PHONE_NUMBER_ID}/messages`,
        {
            messaging_product: 'whatsapp',
            to: to,
            text: { body: text }
        },
        {
            headers: {
                'Authorization': `Bearer ${WHATSAPP_TOKEN}`,
                'Content-Type': 'application/json'
            }
        }
    );
}

app.listen(3000, () => {
    console.log('WhatsApp bot listening on port 3000');
});
```

### Step 4: Docker Configuration (Day 3)
```dockerfile
# fastapi-risk-engine/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# whatsapp-bot/Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000
CMD ["node", "index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  fastapi:
    build: ./fastapi-risk-engine
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    depends_on:
      - redis

  whatsapp-bot:
    build: ./whatsapp-bot
    ports:
      - "3000:3000"
    environment:
      - FASTAPI_URL=http://fastapi:8000
      - WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
      - VERIFY_TOKEN=${VERIFY_TOKEN}
    depends_on:
      - fastapi

volumes:
  redis_data:
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

#### **FastAPI Risk Engine Tests**
```python
# tests/test_risk_engine.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_low_risk_order():
    payload = {
        "order_id": "TEST-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801700000000",
        "delivery_address": {"area": "Gulshan", "city": "Dhaka", "postal_code": "1212"},
        "order_details": {"total_amount": 300, "currency": "BDT", "items_count": 1, "is_first_order": false},
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] <= 40
    assert data["risk_level"] == "LOW"
    assert data["recommendation"] == "PROCEED_WITH_COD"

def test_high_risk_blacklisted():
    # Pre-populate Redis with blacklist
    redis_client.set("blacklist:+8801799999999", "2")
    
    payload = {
        "order_id": "TEST-002",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801799999999",
        "delivery_address": {"area": "Unknown", "city": "Dhaka", "postal_code": ""},
        "order_details": {"total_amount": 1500, "currency": "BDT", "items_count": 3, "is_first_order": true},
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 70
    assert data["risk_level"] == "HIGH"
    assert "ADVANCE_PAYMENT" in data["recommendation"]

def test_performance_under_100ms():
    payload = {...}  # Standard payload
    response = client.post("/api/v1/risk-score", json=payload)
    data = response.json()
    assert data["processing_time_ms"] < 100
```

#### **WhatsApp Bot Tests**
```javascript
// tests/whatsapp.test.js
const request = require('supertest');
const app = require('../index');

describe('WhatsApp Webhook', () => {
    test('Verification challenge', async () => {
        const response = await request(app)
            .get('/webhook/whatsapp')
            .query({
                'hub.mode': 'subscribe',
                'hub.verify_token': process.env.VERIFY_TOKEN,
                'hub.challenge': 'test_challenge'
            });
        
        expect(response.status).toBe(200);
        expect(response.text).toBe('test_challenge');
    });
    
    test('Profit query intent detection', async () => {
        const message = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            text: { body: 'ei mashe labh koto?' }
                        }]
                    }
                }]
            }]
        };
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(message);
        
        expect(response.status).toBe(200);
        // Verify profit query handler was called
    });
});
```

### 5.2 Integration Tests

#### **End-to-End Flow Test**
```python
# tests/test_e2e.py
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

def test_full_risk_assessment_flow():
    # Step 1: Submit order for risk scoring
    order_payload = {
        "order_id": "E2E-TEST-001",
        "merchant_id": "MERCH-E2E",
        "customer_phone": "+8801612345678",
        "delivery_address": {"area": "Mirpur", "city": "Dhaka", "postal_code": "1216"},
        "order_details": {"total_amount": 800, "currency": "BDT", "items_count": 2, "is_first_order": true},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/risk-score", json=order_payload)
    assert response.status_code == 200
    
    risk_data = response.json()
    assert "risk_score" in risk_data
    assert "recommendation" in risk_data
    
    # Step 2: Verify database entry (if storing results)
    # Step 3: Check Redis cache update
    # Step 4: Simulate merchant receiving WhatsApp alert
    
    print(f"✅ E2E Test Passed - Risk Score: {risk_data['risk_score']}")
```

### 5.3 Load Testing

#### **Using Locust for Performance Testing**
```python
# tests/locustfile.py
from locust import HttpUser, task, between

class RiskEngineUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def risk_score_request(self):
        payload = {
            "order_id": f"LOAD-{self.environment.stats.num_requests}",
            "merchant_id": "LOAD-TEST",
            "customer_phone": "+8801700000000",
            "delivery_address": {"area": "Dhanmondi", "city": "Dhaka", "postal_code": "1205"},
            "order_details": {"total_amount": 500, "currency": "BDT", "items_count": 1, "is_first_order": false},
            "timestamp": "2025-12-13T10:00:00Z"
        }
        
        self.client.post("/api/v1/risk-score", json=payload)

# Run: locust -f locustfile.py --host=http://localhost:8000
# Target: 100 requests/sec with <100ms response time
```

### 5.4 Manual Testing Checklist

- [ ] **COD Shield API**
  - [ ] Low risk order (score 0-40) returns correct recommendation
  - [ ] Blacklisted phone triggers high risk (score 70+)
  - [ ] First-time high-value order increases score by 30 points
  - [ ] Response time consistently under 100ms
  - [ ] Invalid phone format returns 400 error

- [ ] **WhatsApp Bot**
  - [ ] Webhook verification completes successfully
  - [ ] "labh koto?" query returns profit data
  - [ ] "risk check +880..." triggers FastAPI call
  - [ ] Image upload acknowledged (saved for Phase 2)
  - [ ] Unknown commands return help message

- [ ] **Database**
  - [ ] Merchant registration creates entry in `merchants` table
  - [ ] Orders stored with correct risk scores
  - [ ] Blacklist queries execute in <50ms

- [ ] **Deployment**
  - [ ] Docker containers start without errors
  - [ ] Services communicate via internal network
  - [ ] Environment variables loaded correctly
  - [ ] Health check endpoints return 200

---

## 6. Test Data & Scenarios

### Test Scenario 1: Legitimate Customer
```json
{
  "order_id": "ORD-LEGIT-001",
  "merchant_id": "MERCH-DEMO",
  "customer_phone": "+8801712345001",
  "delivery_address": {"area": "Gulshan", "city": "Dhaka", "postal_code": "1212"},
  "order_details": {"total_amount": 450, "currency": "BDT", "items_count": 1, "is_first_order": false}
}
```
**Expected Output:**
- Risk Score: 15-25 (LOW)
- Recommendation: PROCEED_WITH_COD

### Test Scenario 2: New Customer, High Value
```json
{
  "order_id": "ORD-NEWRICH-001",
  "customer_phone": "+8801712345002",
  "order_details": {"total_amount": 2500, "is_first_order": true}
}
```
**Expected Output:**
- Risk Score: 45-55 (MEDIUM)
- Recommendation: CONFIRMATION_CALL_REQUIRED

### Test Scenario 3: Blacklisted Fraudster
```json
{
  "customer_phone": "+8801712345003",  // Pre-seed in Redis with 3 hits
  "order_details": {"total_amount": 1200, "is_first_order": true}
}
```
**Expected Output:**
- Risk Score: 85+ (HIGH)
- Recommendation: ADVANCE_PAYMENT_REQUIRED
- Factors: BLACKLISTED_PHONE (60 points), HIGH_VALUE_FIRST_ORDER (30 points)

---

## 7. Monitoring & Observability

### Key Metrics to Track

| Metric | Target | Tool |
|--------|--------|------|
| Risk API Response Time | <100ms (p95) | Prometheus + Grafana |
| WhatsApp Message Latency | <2s end-to-end | Application logs |
| Redis Cache Hit Rate | >90% | Redis INFO command |
| Database Query Time | <50ms (p95) | Supabase dashboard |
| Error Rate | <1% | Sentry |

### Logging Strategy
```python
# Example structured logging
import logging
import json

logger = logging.getLogger("cod_shield")

logger.info(json.dumps({
    "event": "risk_score_calculated",
    "order_id": order.order_id,
    "risk_score": risk_score,
    "processing_time_ms": processing_time,
    "merchant_id": order.merchant_id
}))
```

---

## 8. Deployment Checklist

### Pre-Deployment
- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests validated
- [ ] Load test confirms 100 req/s capacity
- [ ] Environment variables documented
- [ ] Supabase tables created and indexed
- [ ] Redis instance provisioned
- [ ] WhatsApp Business API credentials obtained

### Deployment Steps
```bash
# 1. Build containers
docker-compose build

# 2. Run database migrations
docker-compose run fastapi alembic upgrade head

# 3. Seed test data
docker-compose run fastapi python seed_data.py

# 4. Start services
docker-compose up -d

# 5. Verify health
curl http://localhost:8000/health
curl http://localhost:3000/health

# 6. Configure WhatsApp webhook
# Point to: https://your-domain.com/webhook/whatsapp
```

### Post-Deployment
- [ ] Monitor logs for first 2 hours
- [ ] Test with 3 real merchant accounts
- [ ] Verify WhatsApp message delivery
- [ ] Check Redis memory usage
- [ ] Set up alerting for errors

---

## 9. Success Criteria (Phase 1 MVP)

| Goal | Measurement | Target |
|------|-------------|--------|
| Risk API Accuracy | False positive rate | <15% |
| System Uptime | Availability | 99%+ during demo |
| Response Speed | API latency (p95) | <100ms |
| User Engagement | WhatsApp query responses | 100% success rate |
| Code Quality | Test coverage | >85% |

---

## 10. Known Limitations & Phase 2 Preview

### Phase 1 Limitations
- **Static blacklist:** No auto-learning from merchant feedback
- **Rule-based bot:** No NLP; relies on keyword matching
- **Manual deployment:** No CI/CD pipeline yet
- **Limited integrations:** No Shopify/Daraz sync

### Phase 2 Enhancements (Teaser)
- Implement TrendSeq social scraping (TikTok/FB)
- Add NeuralProphet demand forecasting
- Upgrade to LangGraph for agentic workflows
- Deploy Kafka for real-time event streaming

---

## 11. Quick Start Guide

```bash
# Clone and setup
git clone <repo-url> millionx-mvp
cd millionx-mvp

# Configure environment
cp .env.example .env
# Edit .env with your Supabase, Redis, WhatsApp credentials

# Launch stack
docker-compose up -d

# Run tests
docker-compose run fastapi pytest
docker-compose run whatsapp-bot npm test

# Access services
# FastAPI: http://localhost:8000/docs
# WhatsApp Bot: Configure webhook to http://localhost:3000/webhook/whatsapp
```

---

## 12. Support & Troubleshooting

### Common Issues

**Issue:** Redis connection timeout
**Solution:**
```bash
# Check Redis is running
docker-compose ps redis
# Restart if needed
docker-compose restart redis
```

**Issue:** WhatsApp webhook returns 403
**Solution:** Verify `VERIFY_TOKEN` in `.env` matches Meta App Settings

**Issue:** Risk scores always returning 0
**Solution:** Ensure Redis blacklist is seeded:
```bash
docker-compose exec redis redis-cli
> SET blacklist:+8801799999999 2
```

---

## Appendix: File Structure

```
millionx-mvp/
├── fastapi-risk-engine/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   │   ├── test_risk_engine.py
│   │   └── test_e2e.py
│   └── alembic/  (migrations)
├── whatsapp-bot/
│   ├── index.js
│   ├── package.json
│   ├── Dockerfile
│   └── tests/
│       └── whatsapp.test.js
├── shared/
│   └── schemas.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

**Document Version:** 1.0  
**Last Updated:** December 13, 2025  
**Status:** Ready for Implementation  

---

### Next Actions
1. Review this plan with the team
2. Set up Supabase project and obtain credentials
3. Register WhatsApp Business API account
4. Begin Day 0 environment setup
5. Schedule daily standups during sprint

**Questions?** Refer to [proposal.txt](proposal.txt) and [plan.txt](plan.txt) for context.
