# Phase 1: Step-by-Step Implementation Tasks

## 📋 Task Overview
This document breaks down the Phase 1 MVP implementation into actionable tasks with clear deliverables and acceptance criteria.

**Estimated Timeline:** 3-4 days (Hackathon Sprint)  
**Team Size:** 2-3 developers  
**End Goal:** Working COD Shield API + WhatsApp Bot Demo

---

## 🏗️ Day 0: Project Setup & Environment Configuration

### Task 0.1: Initialize Project Structure
**Owner:** Backend Lead  
**Duration:** 30 minutes  
**Priority:** P0 (Blocker)

#### Steps:
```bash
# 1. Create root directory
cd c:\Users\Legion\OneDrive\Desktop\millionx
mkdir millionx-mvp
cd millionx-mvp

# 2. Create service directories
mkdir fastapi-risk-engine
mkdir whatsapp-bot
mkdir shared
mkdir tests

# 3. Initialize git repository
git init
git branch -M main
```

#### Deliverables:
- [ ] Project folder structure created
- [ ] Git repository initialized
- [ ] `.gitignore` file created

#### Acceptance Criteria:
- Directory structure matches the plan
- Git repository is ready for commits

---

### Task 0.2: Setup Supabase Project
**Owner:** Backend Lead  
**Duration:** 20 minutes  
**Priority:** P0 (Blocker)

#### Steps:
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in details:
   - Project Name: `millionx-mvp`
   - Database Password: (Generate strong password)
   - Region: Southeast Asia (Singapore)
4. Wait for provisioning (~2 minutes)
5. Navigate to Settings → API
6. Copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

#### Deliverables:
- [ ] Supabase project created
- [ ] Database credentials saved securely
- [ ] API keys documented

#### Acceptance Criteria:
- Can access Supabase dashboard
- Database is running and accessible

---

### Task 0.3: Setup Redis Instance
**Owner:** DevOps/Backend  
**Duration:** 15 minutes  
**Priority:** P0 (Blocker)

#### Steps:
**Option A: Local Docker (Recommended for Development)**
```bash
docker run -d --name millionx-redis -p 6379:6379 redis:7-alpine
```

**Option B: Cloud Redis (Production)**
- Use Upstash (Free tier: https://upstash.com/)
- Or Redis Cloud (https://redis.com/try-free/)

#### Deliverables:
- [ ] Redis instance running
- [ ] Connection tested successfully
- [ ] Connection string saved

#### Acceptance Criteria:
```bash
# Test connection
redis-cli ping
# Should return: PONG
```

---

### Task 0.4: WhatsApp Business API Setup
**Owner:** Frontend/Integration Lead  
**Duration:** 45 minutes  
**Priority:** P0 (Blocker)

#### Steps:
1. Go to https://developers.facebook.com/
2. Create a new app → Business Type
3. Add "WhatsApp" product
4. Navigate to WhatsApp → Getting Started
5. Add a test phone number
6. Generate temporary access token (24h validity)
7. Copy:
   - Phone Number ID
   - WhatsApp Business Account ID
   - Access Token
8. Configure webhook (will set URL later)

#### Deliverables:
- [ ] Meta Developer Account created
- [ ] WhatsApp Business API app configured
- [ ] Test phone number added
- [ ] Access token generated

#### Acceptance Criteria:
- Can send test message via API Playground
- Webhook verification pending (will complete in Day 2)

---

### Task 0.5: Create Environment Configuration
**Owner:** Backend Lead  
**Duration:** 15 minutes  
**Priority:** P0 (Blocker)

#### Steps:
Create `.env` file in project root:

```bash
# .env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# WhatsApp
WHATSAPP_TOKEN=your_temp_token
VERIFY_TOKEN=your_custom_secret_123
PHONE_NUMBER_ID=your_phone_number_id

# FastAPI
FASTAPI_URL=http://localhost:8000
```

Create `.env.example` (without secrets) for git:
```bash
cp .env .env.example
# Remove actual values from .env.example
```

#### Deliverables:
- [ ] `.env` file created with all credentials
- [ ] `.env.example` template created
- [ ] `.env` added to `.gitignore`

#### Acceptance Criteria:
- All required environment variables documented
- Sensitive data not committed to git

---

## 🔧 Day 1: FastAPI Risk Engine Development

### Task 1.1: Setup FastAPI Project
**Owner:** Backend Developer 1  
**Duration:** 30 minutes  
**Priority:** P0

#### Steps:
```bash
cd fastapi-risk-engine

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Create requirements.txt
```

**requirements.txt:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
redis==5.0.1
supabase==2.0.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

```bash
# Install dependencies
pip install -r requirements.txt
```

#### Deliverables:
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `requirements.txt` finalized

#### Acceptance Criteria:
```bash
pip list | grep fastapi
# Should show fastapi 0.104.1
```

---

### Task 1.2: Implement COD Shield Core Logic
**Owner:** Backend Developer 1  
**Duration:** 2 hours  
**Priority:** P0

#### Steps:
Create `fastapi-risk-engine/main.py` with the following components:

**Part A: Data Models (30 min)**
```python
from pydantic import BaseModel
from typing import List, Dict

class DeliveryAddress(BaseModel):
    area: str
    city: str
    postal_code: str

class OrderDetails(BaseModel):
    total_amount: float
    currency: str
    items_count: int
    is_first_order: bool

class OrderData(BaseModel):
    order_id: str
    merchant_id: str
    customer_phone: str
    delivery_address: DeliveryAddress
    order_details: OrderDetails
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
```

**Part B: Redis Connection (15 min)**
```python
import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', None),
    decode_responses=True
)
```

**Part C: Risk Calculation Function (45 min)**
```python
def calculate_risk_score(order: OrderData) -> tuple[int, List[RiskFactor]]:
    """
    Calculate risk score based on multiple factors.
    Returns: (risk_score, list_of_factors)
    """
    risk_score = 0
    factors = []
    
    # Factor 1: Blacklist Check (0-60 points)
    blacklist_key = f"blacklist:{order.customer_phone}"
    blacklist_hits = redis_client.get(blacklist_key)
    
    if blacklist_hits:
        hits = int(blacklist_hits)
        weight = min(hits * 30, 60)
        risk_score += weight
        factors.append(RiskFactor(
            factor="BLACKLISTED_PHONE",
            weight=weight,
            description=f"Phone has {hits} previous failed deliveries"
        ))
    
    # Factor 2: First Order + High Value (0-30 points)
    if order.order_details.is_first_order:
        amount = order.order_details.total_amount
        if amount > 1000:
            weight = 30
            risk_score += weight
            factors.append(RiskFactor(
                factor="HIGH_VALUE_FIRST_ORDER",
                weight=weight,
                description=f"Order amount Tk {amount} for new customer"
            ))
        elif amount > 500:
            weight = 15
            risk_score += weight
            factors.append(RiskFactor(
                factor="MEDIUM_VALUE_FIRST_ORDER",
                weight=weight,
                description=f"Order amount Tk {amount} for new customer"
            ))
    
    # Factor 3: Address Risk (0-20 points)
    risky_areas = ['Unknown', 'Remote', 'N/A']
    if order.delivery_address.area in risky_areas:
        weight = 20
        risk_score += weight
        factors.append(RiskFactor(
            factor="RISKY_DELIVERY_AREA",
            weight=weight,
            description="Delivery to high-risk or unverified area"
        ))
    
    # Factor 4: Time Anomaly (0-10 points)
    from datetime import datetime
    order_time = datetime.fromisoformat(order.timestamp.replace('Z', '+00:00'))
    hour = order_time.hour
    if 2 <= hour <= 5:  # 2 AM - 5 AM
        weight = 10
        risk_score += weight
        factors.append(RiskFactor(
            factor="SUSPICIOUS_TIME",
            weight=weight,
            description=f"Order placed at {hour}:00 (unusual hours)"
        ))
    
    return min(risk_score, 100), factors
```

**Part D: FastAPI Endpoint (30 min)**
```python
from fastapi import FastAPI, HTTPException
import time

app = FastAPI(
    title="COD Shield API",
    description="Real-time COD fraud detection for South Asian e-commerce",
    version="1.0.0"
)

@app.post("/api/v1/risk-score", response_model=RiskResponse)
async def assess_risk(order: OrderData):
    """
    Assess COD fraud risk for an order.
    
    Returns risk score (0-100) with recommendations.
    """
    start_time = time.time()
    
    try:
        risk_score, factors = calculate_risk_score(order)
        
        # Determine risk level and recommendation
        if risk_score <= 40:
            risk_level = "LOW"
            recommendation = "PROCEED_WITH_COD"
            actions = ["Process order normally", "Standard delivery procedure"]
        elif risk_score <= 70:
            risk_level = "MEDIUM"
            recommendation = "CONFIRMATION_CALL_REQUIRED"
            actions = [
                "Call customer to confirm order",
                "Verify delivery address",
                "Consider photo verification on delivery"
            ]
        else:
            risk_level = "HIGH"
            recommendation = "ADVANCE_PAYMENT_REQUIRED"
            actions = [
                "Request 50% advance payment via bKash/Nagad",
                "Limit COD to maximum Tk 500",
                "Require valid NID/passport copy"
            ]
        
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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk calculation failed: {str(e)}")

@app.post("/api/v1/blacklist")
async def add_to_blacklist(request: dict):
    """
    Add a phone number to the blacklist.
    Enables merchants to report fraudsters (Network Effect!).
    """
    try:
        phone = request.get('customer_phone')
        reason = request.get('reason', 'Reported by merchant')
        merchant_id = request.get('merchant_id', 'UNKNOWN')
        
        if not phone:
            raise HTTPException(status_code=400, detail="customer_phone is required")
        
        # Check if phone already in blacklist
        blacklist_key = f"blacklist:{phone}"
        current_hits = redis_client.get(blacklist_key)
        
        if current_hits:
            new_hits = int(current_hits) + 1
            redis_client.set(blacklist_key, new_hits)
            message = f"Phone {phone} blacklist updated to {new_hits} incidents"
        else:
            redis_client.set(blacklist_key, 1)
            message = f"Phone {phone} added to blacklist"
        
        # Set TTL of 30 days
        redis_client.expire(blacklist_key, 60 * 60 * 24 * 30)
        
        return {
            "success": True,
            "message": message,
            "phone": phone,
            "total_reports": int(redis_client.get(blacklist_key)),
            "reported_by": merchant_id,
            "reason": reason
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to blacklist: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.ping()
        return {
            "status": "healthy",
            "service": "COD Shield",
            "version": "1.0.0",
            "redis": "connected"
        }
    except:
        return {
            "status": "degraded",
            "service": "COD Shield",
            "version": "1.0.0",
            "redis": "disconnected"
        }

@app.get("/")
async def root():
    return {
        "message": "COD Shield API",
        "docs": "/docs",
        "health": "/health"
    }
```

#### Deliverables:
- [ ] `main.py` file created with all endpoints
- [ ] Risk calculation logic implemented
- [ ] Redis integration working
- [ ] **Blacklist reporting endpoint added (POST /api/v1/blacklist)**

#### Acceptance Criteria:
```bash
# Start the server
uvicorn main:app --reload

# Server starts successfully
# Available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

---

### Task 1.3: Create Seed Data for Testing
**Owner:** Backend Developer 1  
**Duration:** 20 minutes  
**Priority:** P1

#### Steps:
Create `fastapi-risk-engine/seed_data.py`:

```python
import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

def seed_blacklist():
    """Seed Redis with test blacklist data"""
    blacklist_data = [
        ("+8801799999999", 3),  # High risk - 3 failed deliveries
        ("+8801788888888", 2),  # Medium-high risk
        ("+8801777777777", 1),  # Low risk
    ]
    
    for phone, hits in blacklist_data:
        redis_client.set(f"blacklist:{phone}", hits)
        print(f"✅ Added {phone} with {hits} hit(s)")
    
    print(f"\n✅ Seeded {len(blacklist_data)} blacklist entries")

if __name__ == "__main__":
    seed_blacklist()
```

#### Deliverables:
- [ ] `seed_data.py` created
- [ ] Test blacklist numbers added to Redis

#### Acceptance Criteria:
```bash
python seed_data.py
# Should output: ✅ Seeded 3 blacklist entries

# Verify in Redis
redis-cli
> GET blacklist:+8801799999999
# Should return: "3"
```

---

### Task 1.4: Write Unit Tests for Risk Engine
**Owner:** Backend Developer 2  
**Duration:** 1.5 hours  
**Priority:** P1

#### Steps:
Create `fastapi-risk-engine/tests/test_risk_engine.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app, redis_client

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_redis():
    """Setup test data before each test"""
    # Clear Redis
    redis_client.flushdb()
    # Seed test data
    redis_client.set("blacklist:+8801799999999", "2")
    yield
    # Cleanup after test
    redis_client.flushdb()

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "COD Shield"

def test_low_risk_order():
    """Test low risk order scenario"""
    payload = {
        "order_id": "TEST-LOW-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801700000000",
        "delivery_address": {
            "area": "Gulshan",
            "city": "Dhaka",
            "postal_code": "1212"
        },
        "order_details": {
            "total_amount": 300,
            "currency": "BDT",
            "items_count": 1,
            "is_first_order": False
        },
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["order_id"] == "TEST-LOW-001"
    assert data["risk_score"] <= 40
    assert data["risk_level"] == "LOW"
    assert data["recommendation"] == "PROCEED_WITH_COD"
    assert data["processing_time_ms"] < 100

def test_high_risk_blacklisted():
    """Test high risk order with blacklisted phone"""
    payload = {
        "order_id": "TEST-HIGH-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801799999999",
        "delivery_address": {
            "area": "Unknown",
            "city": "Dhaka",
            "postal_code": ""
        },
        "order_details": {
            "total_amount": 1500,
            "currency": "BDT",
            "items_count": 3,
            "is_first_order": True
        },
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["risk_score"] > 70
    assert data["risk_level"] == "HIGH"
    assert "ADVANCE_PAYMENT" in data["recommendation"]
    
    # Check factors
    factor_types = [f["factor"] for f in data["factors"]]
    assert "BLACKLISTED_PHONE" in factor_types

def test_medium_risk_new_customer():
    """Test medium risk order - new customer with moderate value"""
    payload = {
        "order_id": "TEST-MED-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801712345678",
        "delivery_address": {
            "area": "Mirpur",
            "city": "Dhaka",
            "postal_code": "1216"
        },
        "order_details": {
            "total_amount": 800,
            "currency": "BDT",
            "items_count": 2,
            "is_first_order": True
        },
        "timestamp": "2025-12-13T14:30:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert 41 <= data["risk_score"] <= 70
    assert data["risk_level"] == "MEDIUM"

def test_suspicious_time_factor():
    """Test time-based risk factor"""
    payload = {
        "order_id": "TEST-TIME-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801700000000",
        "delivery_address": {
            "area": "Dhanmondi",
            "city": "Dhaka",
            "postal_code": "1205"
        },
        "order_details": {
            "total_amount": 500,
            "currency": "BDT",
            "items_count": 1,
            "is_first_order": False
        },
        "timestamp": "2025-12-13T03:30:00Z"  # 3:30 AM
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    factor_types = [f["factor"] for f in data["factors"]]
    assert "SUSPICIOUS_TIME" in factor_types

def test_performance_benchmark():
    """Test API response time"""
    payload = {
        "order_id": "TEST-PERF-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801700000000",
        "delivery_address": {
            "area": "Banani",
            "city": "Dhaka",
            "postal_code": "1213"
        },
        "order_details": {
            "total_amount": 500,
            "currency": "BDT",
            "items_count": 1,
            "is_first_order": False
        },
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    response = client.post("/api/v1/risk-score", json=payload)
    data = response.json()
    
    # Should process in under 100ms
    assert data["processing_time_ms"] < 100
```

#### Deliverables:
- [ ] Test file created with 7 test cases
- [ ] All tests passing

#### Acceptance Criteria:
```bash
cd fastapi-risk-engine
pytest -v

# Should show:
# test_health_endpoint PASSED
# test_low_risk_order PASSED
# test_high_risk_blacklisted PASSED
# test_medium_risk_new_customer PASSED
# test_suspicious_time_factor PASSED
# test_performance_benchmark PASSED
# ====== 7 passed in X.XXs ======
```

---

## 📱 Day 2: WhatsApp Bot Development

### Task 2.1: Setup Node.js Project
**Owner:** Backend Developer 2  
**Duration:** 20 minutes  
**Priority:** P0

#### Steps:
```bash
cd whatsapp-bot

# Initialize npm project
npm init -y

# Install dependencies
npm install express axios dotenv redis @supabase/supabase-js

# Install dev dependencies
npm install --save-dev jest supertest nodemon
```

Update `package.json`:
```json
{
  "name": "millionx-whatsapp-bot",
  "version": "1.0.0",
  "description": "WhatsApp Business API integration for MillionX",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.6.2",
    "dotenv": "^16.3.1",
    "redis": "^4.6.11",
    "@supabase/supabase-js": "^2.39.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "nodemon": "^3.0.2"
  }
}
```

#### Deliverables:
- [ ] `package.json` configured
- [ ] Dependencies installed
- [ ] Dev environment ready

#### Acceptance Criteria:
```bash
node --version
# Should show v18.x or higher

npm list express
# Should show express@4.18.2
```

---

### Task 2.2: Implement WhatsApp Webhook Handler
**Owner:** Backend Developer 2  
**Duration:** 2 hours  
**Priority:** P0

#### Steps:
Create `whatsapp-bot/index.js`:

```javascript
const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const WHATSAPP_TOKEN = process.env.WHATSAPP_TOKEN;
const VERIFY_TOKEN = process.env.VERIFY_TOKEN;
const PHONE_NUMBER_ID = process.env.PHONE_NUMBER_ID;

// ============= WEBHOOK VERIFICATION =============
app.get('/webhook/whatsapp', (req, res) => {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];
    
    console.log('📞 Webhook verification request received');
    
    if (mode === 'subscribe' && token === VERIFY_TOKEN) {
        console.log('✅ Webhook verified successfully');
        res.status(200).send(challenge);
    } else {
        console.log('❌ Webhook verification failed');
        res.sendStatus(403);
    }
});

// ============= MESSAGE HANDLER =============
app.post('/webhook/whatsapp', async (req, res) => {
    try {
        console.log('📨 Incoming webhook:', JSON.stringify(req.body, null, 2));
        
        // Extract message data
        const entry = req.body.entry?.[0];
        const changes = entry?.changes?.[0];
        const value = changes?.value;
        const messages = value?.messages;
        
        if (!messages || messages.length === 0) {
            console.log('ℹ️  No messages in webhook (likely a status update)');
            return res.sendStatus(200);
        }
        
        const message = messages[0];
        const from = message.from;
        const messageType = message.type;
        
        let response = '';
        
        // Route based on message type
        if (messageType === 'text') {
            const text = message.text.body.toLowerCase();
            response = await routeTextMessage(text, from);
        } else if (messageType === 'image') {
            response = await handleImageUpload(message, from);
        } else {
            response = '🤖 Sorry, I can only handle text messages and images for now.';
        }
        
        // Send response
        await sendWhatsAppMessage(from, response);
        
        res.sendStatus(200);
    } catch (error) {
        console.error('❌ Error processing message:', error);
        res.sendStatus(500);
    }
});

// ============= MESSAGE ROUTING =============
async function routeTextMessage(text, from) {
    console.log(`🔍 Routing message: "${text}" from ${from}`);
    
    // Intent: Profit/Revenue Query
    if (text.match(/labh|profit|income|revenue|earning/)) {
        return await handleProfitQuery(from);
    }
    
    // Intent: Inventory Check
    if (text.match(/inventory|stock|product/)) {
        return await handleInventoryQuery(from);
    }
    
    // Intent: Risk Check
    if (text.match(/risk check/)) {
        const phone = extractPhoneNumber(text);
        if (phone) {
            return await handleRiskCheck(phone);
        } else {
            return '❌ Please provide phone number.\nExample: "risk check +8801712345678"';
        }
    }
    
    // Intent: Report Fraudster (NETWORK EFFECT!)
    if (text.match(/report/)) {
        const phone = extractPhoneNumber(text);
        if (phone) {
            return await handleReportFraudster(phone, from);
        } else {
            return '❌ Please provide phone number to report.\nExample: "report +8801712345678"';
        }
    }
    
    // Default: Help message
    return getHelpMessage();
}

// ============= INTENT HANDLERS =============
async function handleProfitQuery(merchantPhone) {
    console.log(`💰 Handling profit query for ${merchantPhone}`);
    
    // TODO: Query Supabase for actual data
    // For MVP, return mock data
    return `📊 *December Profit Summary*\n\n` +
           `💰 Revenue: Tk 45,300\n` +
           `💸 Costs: Tk 32,100\n` +
           `✅ *Net Profit: Tk 13,200* (+18% vs Nov)\n\n` +
           `🔥 Top seller: Blue T-shirt (45 units)\n` +
           `📦 Total orders: 127`;
}

async function handleInventoryQuery(merchantPhone) {
    console.log(`📦 Handling inventory query for ${merchantPhone}`);
    
    // TODO: Query actual inventory from database
    // For MVP, return mock data
    return `📦 *Inventory Alert*\n\n` +
           `⚠️ *Low Stock Items:*\n` +
           `• Blue T-shirt - 8 left\n` +
           `• Red Hoodie - 5 left\n` +
           `• Black Cap - 3 left\n\n` +
           `💡 Tip: Restock Blue T-shirt soon (trending!)`;
}

async function handleRiskCheck(phone) {
    console.log(`🛡️ Checking risk for ${phone}`);
    
    try {
        const response = await axios.post(`${FASTAPI_URL}/api/v1/risk-score`, {
            order_id: `MANUAL-${Date.now()}`,
            merchant_id: 'DEMO-MERCHANT',
            customer_phone: phone,
            delivery_address: {
                area: 'Unknown',
                city: 'Dhaka',
                postal_code: ''
            },
            order_details: {
                total_amount: 500,
                currency: 'BDT',
                items_count: 1,
                is_first_order: false
            },
            timestamp: new Date().toISOString()
        });
        
        const data = response.data;
        
        return `🛡️ *COD Risk Check*\n\n` +
               `📱 Phone: ${phone}\n` +
               `📊 Risk Score: ${data.risk_score}/100\n` +
               `⚠️ Level: *${data.risk_level}*\n` +
               `💡 Recommendation: ${data.recommendation.replace(/_/g, ' ')}\n\n` +
               `*Suggested Actions:*\n` +
               data.suggested_actions.map(a => `• ${a}`).join('\n');
        
    } catch (error) {
        console.error('Error calling FastAPI:', error.message);
        return '❌ Risk check failed. Please try again or contact support.';
    }
}

async function handleImageUpload(message, from) {
    console.log(`🖼️  Image received from ${from}`);
    
    // TODO: Download image and process in Phase 2
    // For MVP, just acknowledge
    return `✅ *Image received!*\n\n` +
           `📸 We've saved your product image.\n` +
           `🔄 Auto-catalog feature coming in Phase 2!\n\n` +
           `For now, you can:\n` +
           `• Check profit: "labh koto?"\n` +
           `• Check stock: "inventory check"`;
}

async function handleReportFraudster(phone, merchantPhone) {
    console.log(`🚨 Reporting fraudster ${phone} by merchant ${merchantPhone}`);
    
    try {
        const response = await axios.post(`${FASTAPI_URL}/api/v1/blacklist`, {
            customer_phone: phone,
            merchant_id: merchantPhone,
            reason: 'Reported by merchant via WhatsApp'
        });
        
        const data = response.data;
        
        return `🚨 *Fraudster Reported!*\n\n` +
               `📱 Phone: ${phone}\n` +
               `✅ Added to network blacklist\n` +
               `📊 Total Reports: ${data.total_reports}\n\n` +
               `🛡️ *You're helping protect the community!*\n` +
               `All merchants will now be warned about this number.\n\n` +
               `💪 Network Effect: ${data.total_reports} merchant(s) protected!`;
        
    } catch (error) {
        console.error('Error reporting fraudster:', error.message);
        return '❌ Failed to report fraudster. Please try again or contact support.';
    }
}

// ============= HELPERS =============
function extractPhoneNumber(text) {
    // Extract Bangladesh phone number format
    const match = text.match(/\+880\d{10}|\b01\d{9}\b/);
    if (match) {
        let phone = match[0];
        // Normalize to international format
        if (phone.startsWith('01')) {
            phone = '+880' + phone.substring(1);
        }
        return phone;
    }
    return null;
}

function getHelpMessage() {
    return `🤖 *Bhai-Bot here!*\n\n` +
           `I can help you with:\n\n` +
           `💰 *Check Profit*\n` +
           `Type: "labh koto?" or "profit"\n\n` +
           `📦 *Check Inventory*\n` +
           `Type: "inventory check" or "stock"\n\n` +
           `🛡️ *COD Risk Check*\n` +
           `Type: "risk check +8801XXXXXXX"\n\n` +
           `� *Report Fraudster* (NEW!)\n` +
           `Type: "report +8801XXXXXXX"\n` +
           `Help protect all merchants!\n\n` +
           `�📸 *Upload Product Image*\n` +
           `Just send an image (cataloging soon!)\n\n` +
           `Need help? Just type "help"`;
}

async function sendWhatsAppMessage(to, text) {
    const url = `https://graph.facebook.com/v18.0/${PHONE_NUMBER_ID}/messages`;
    
    try {
        await axios.post(
            url,
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
        console.log(`✅ Message sent to ${to}`);
    } catch (error) {
        console.error('❌ Failed to send WhatsApp message:', error.response?.data || error.message);
        throw error;
    }
}

// ============= HEALTH CHECK =============
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'WhatsApp Bot',
        version: '1.0.0'
    });
});

// ============= START SERVER =============
app.listen(PORT, () => {
    console.log(`🚀 WhatsApp Bot running on port ${PORT}`);
    console.log(`📱 Webhook URL: http://localhost:${PORT}/webhook/whatsapp`);
    console.log(`🏥 Health check: http://localhost:${PORT}/health`);
});

module.exports = app;
```

#### Deliverables:
- [ ] `index.js` with full webhook implementation
- [ ] Message routing logic complete
- [ ] Integration with FastAPI risk endpoint
- [ ] **Report fraudster handler added (calls POST /api/v1/blacklist)**

#### Acceptance Criteria:
```bash
npm run dev
# Server starts on port 3000
# No errors in console
```

---

### Task 2.3: Configure WhatsApp Webhook (Production)
**Owner:** DevOps/Backend  
**Duration:** 30 minutes  
**Priority:** P1

#### Steps:
**Option A: ngrok (Quick Testing)**
```bash
# Install ngrok
choco install ngrok  # Windows
# or download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option B: Deploy to Cloud (Recommended)**
- Deploy to Railway/Render/DigitalOcean
- Get public HTTPS URL

**Configure in Meta:**
1. Go to Meta Developer Dashboard
2. WhatsApp → Configuration
3. Webhook settings:
   - Callback URL: `https://your-domain.com/webhook/whatsapp`
   - Verify Token: (same as in `.env`)
4. Subscribe to: `messages`
5. Click "Verify and Save"

#### Deliverables:
- [ ] Webhook publicly accessible via HTTPS
- [ ] Webhook verified in Meta dashboard
- [ ] Message subscription active

#### Acceptance Criteria:
- Meta shows "✅ Webhook verified"
- Test message from WhatsApp triggers the bot

---

### Task 2.4: Integration Testing
**Owner:** QA/Backend Developer  
**Duration:** 1 hour  
**Priority:** P1

#### Steps:
Create `whatsapp-bot/tests/integration.test.js`:

```javascript
const request = require('supertest');
const app = require('../index');

describe('WhatsApp Bot Integration Tests', () => {
    
    test('GET /health returns healthy status', async () => {
        const response = await request(app).get('/health');
        expect(response.status).toBe(200);
        expect(response.body.status).toBe('healthy');
    });
    
    test('GET /webhook/whatsapp verifies correctly', async () => {
        const response = await request(app)
            .get('/webhook/whatsapp')
            .query({
                'hub.mode': 'subscribe',
                'hub.verify_token': process.env.VERIFY_TOKEN,
                'hub.challenge': 'test_challenge_123'
            });
        
        expect(response.status).toBe(200);
        expect(response.text).toBe('test_challenge_123');
    });
    
    test('POST /webhook/whatsapp handles profit query', async () => {
        const mockMessage = {
            entry: [{
                changes: [{
                    value: {
                        messages: [{
                            from: '+8801712345678',
                            type: 'text',
                            text: { body: 'labh koto?' }
                        }]
                    }
                }]
            }]
        };
        
        const response = await request(app)
            .post('/webhook/whatsapp')
            .send(mockMessage);
        
        expect(response.status).toBe(200);
    });
    
});
```

Run tests:
```bash
npm test
```

#### Deliverables:
- [ ] Integration test suite created
- [ ] All tests passing

#### Acceptance Criteria:
```bash
npm test
# All tests pass
```

---

## 🐳 Day 3: Containerization & Deployment

### Task 3.1: Create Dockerfiles
**Owner:** DevOps  
**Duration:** 45 minutes  
**Priority:** P0

#### Steps:

**File 1: `fastapi-risk-engine/Dockerfile`**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File 2: `whatsapp-bot/Dockerfile`**
```dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Run application
CMD ["node", "index.js"]
```

**File 3: `docker-compose.yml` (root directory)**
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: millionx-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  fastapi:
    build:
      context: ./fastapi-risk-engine
      dockerfile: Dockerfile
    container_name: millionx-fastapi
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

  whatsapp-bot:
    build:
      context: ./whatsapp-bot
      dockerfile: Dockerfile
    container_name: millionx-whatsapp-bot
    ports:
      - "3000:3000"
    environment:
      - FASTAPI_URL=http://fastapi:8000
      - WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
      - VERIFY_TOKEN=${VERIFY_TOKEN}
      - PHONE_NUMBER_ID=${PHONE_NUMBER_ID}
    depends_on:
      - fastapi
    restart: unless-stopped

volumes:
  redis_data:
    driver: local

networks:
  default:
    name: millionx-network
```

#### Deliverables:
- [ ] All Dockerfiles created
- [ ] docker-compose.yml configured
- [ ] Health checks implemented

#### Acceptance Criteria:
```bash
docker-compose config
# No errors, shows compiled config
```

---

### Task 3.2: Build and Test Containers
**Owner:** DevOps  
**Duration:** 30 minutes  
**Priority:** P0

#### Steps:
```bash
# Build all containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/health
```

#### Deliverables:
- [ ] All containers build successfully
- [ ] Services start without errors
- [ ] Health checks return healthy status

#### Acceptance Criteria:
```bash
docker-compose ps
# All services show "healthy" status
```

---

### Task 3.3: Setup Supabase Database Tables
**Owner:** Backend Lead  
**Duration:** 30 minutes  
**Priority:** P1

#### Steps:
1. Go to Supabase Dashboard → SQL Editor
2. Run the following SQL:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create merchants table
CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    registration_date TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_area VARCHAR(100),
    delivery_city VARCHAR(50),
    delivery_postal_code VARCHAR(20),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(20) DEFAULT 'COD',
    items_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create blacklist table
CREATE TABLE blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    failed_deliveries INTEGER DEFAULT 1,
    total_fraud_amount DECIMAL(10,2) DEFAULT 0,
    last_incident_date TIMESTAMPTZ,
    reason TEXT,
    added_by UUID REFERENCES merchants(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX idx_orders_merchant_id ON orders(merchant_id);
CREATE INDEX idx_orders_risk_score ON orders(risk_score);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_blacklist_phone ON blacklist(phone);

-- Insert test merchant
INSERT INTO merchants (phone, business_name) 
VALUES ('+8801712345678', 'Test Merchant Store');

-- Insert test orders
INSERT INTO orders (merchant_id, order_id, customer_phone, total_amount, delivery_area, delivery_city, status, items_count)
SELECT 
    m.id,
    'ORD-' || generate_series(1, 10),
    '+88017000000' || generate_series(1, 10),
    (random() * 2000 + 100)::DECIMAL(10,2),
    CASE (random() * 3)::int 
        WHEN 0 THEN 'Gulshan'
        WHEN 1 THEN 'Dhanmondi'
        ELSE 'Mirpur'
    END,
    'Dhaka',
    'completed',
    (random() * 5 + 1)::int
FROM merchants m
LIMIT 1;

-- Insert test blacklist entries
INSERT INTO blacklist (phone, failed_deliveries, total_fraud_amount, last_incident_date, reason)
VALUES 
    ('+8801799999999', 3, 4500.00, NOW() - INTERVAL '2 days', 'Multiple failed deliveries'),
    ('+8801788888888', 2, 2100.00, NOW() - INTERVAL '1 week', 'Refused payment'),
    ('+8801777777777', 1, 800.00, NOW() - INTERVAL '1 month', 'Address not found');

-- Verify data
SELECT 'Merchants' as table_name, COUNT(*) as count FROM merchants
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Blacklist', COUNT(*) FROM blacklist;
```

#### Deliverables:
- [ ] All tables created in Supabase
- [ ] Indexes created
- [ ] Test data inserted

#### Acceptance Criteria:
- Query returns counts for all tables
- Can view data in Supabase Table Editor

---

### Task 3.4: End-to-End System Test
**Owner:** Full Team  
**Duration:** 1 hour  
**Priority:** P0

#### Test Scenarios:

**Scenario 1: Low Risk Order**
```bash
# Send to FastAPI
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "E2E-TEST-001",
    "merchant_id": "MERCH-001",
    "customer_phone": "+8801700000001",
    "delivery_address": {
      "area": "Gulshan",
      "city": "Dhaka",
      "postal_code": "1212"
    },
    "order_details": {
      "total_amount": 400,
      "currency": "BDT",
      "items_count": 1,
      "is_first_order": false
    },
    "timestamp": "2025-12-13T10:00:00Z"
  }'

# Expected: risk_score <= 40, risk_level: "LOW"
```

**Scenario 2: High Risk Order via WhatsApp**
1. Send WhatsApp message to bot: "risk check +8801799999999"
2. Expected response: Risk score 60+, HIGH level, advance payment required

**Scenario 3: Profit Query**
1. Send WhatsApp message: "labh koto?"
2. Expected response: Profit summary with mock data

**Scenario 4: Report Fraudster (Network Effect Test)**
1. Send WhatsApp message: "report +8801799999999"
2. Expected response: Confirmation with total reports count
3. Verify: Send "risk check +8801799999999" - should show increased blacklist hits

#### Deliverables:
- [ ] All 4 scenarios tested successfully
- [ ] Response times under 2 seconds
- [ ] No errors in logs
- [ ] **Blacklist updates reflected in subsequent risk checks**

#### Acceptance Criteria:
- All API endpoints respond correctly
- WhatsApp messages delivered
- Docker logs show no errors

---

## 🚀 Day 4: Demo Preparation & Documentation

### Task 4.1: Create Demo Script
**Owner:** Product/Team Lead  
**Duration:** 1 hour  
**Priority:** P0

Create `DEMO.md`:

```markdown
# MillionX MVP Demo Script

## Setup (5 minutes before demo)
1. Ensure all Docker containers running
2. Open terminals: FastAPI logs, WhatsApp bot logs
3. Have WhatsApp open on phone
4. Open Postman/browser with FastAPI docs

## Demo Flow (10 minutes)

### Part 1: COD Shield API (3 min)
**Scenario:** Show risk scoring for different order types

1. **Low Risk Order**
   - Open http://localhost:8000/docs
   - Test with good customer
   - Show risk score: 10-20, LOW
   - "This customer is safe for COD"

2. **High Risk Order**
   - Test with blacklisted number: +8801799999999
   - Show risk score: 80+, HIGH
   - "System recommends advance payment"

3. **API Performance**
   - Point to processing_time_ms < 100
   - "Real-time risk assessment"

### Part 2: WhatsApp Integration (5 min)
**Scenario:** Merchant managing business via WhatsApp

1. **Profit Check**
   - Send: "labh koto?"
   - Show instant profit summary
   - "Merchant gets insights in Bangla"

2. **Risk Check**
   - Send: "risk check +8801799999999"
   - Show detailed risk report
   - "Proactive fraud prevention"

3. **Inventory Alert**
   - Send: "inventory check"
   - Show low stock warning
   - "Never run out of trending items"

4. **Report Fraudster (Network Effect!)**
   - Send: "report +8801799999999"
   - Show confirmation with network count
   - Send: "risk check +8801799999999"
   - Show blacklist increased
   - "One merchant reports, ALL merchants protected!"

### Part 3: System Architecture (2 min)
- Show docker-compose ps (all services healthy)
- Explain: FastAPI (ML), Redis (cache), WhatsApp (interface)
- "Scalable, production-ready architecture"

## Key Messages
✅ Real-time COD fraud detection  
✅ WhatsApp-native (no app needed)  
✅ Works in Bangla (Benglish)  
✅ Response time < 100ms  
✅ **Network Effect: One report protects ALL merchants**  
✅ Ready for 50+ merchants
```

#### Deliverables:
- [ ] Demo script created
- [ ] Demo tested with team
- [ ] Backup scenarios prepared

---

### Task 4.2: Create README Documentation
**Owner:** Technical Writer/Developer  
**Duration:** 45 minutes  
**Priority:** P1

Create `README.md` in project root:

```markdown
# MillionX MVP - Commerce Intelligence Platform

COD fraud detection and WhatsApp-based business intelligence for South Asian SMEs.

## 🚀 Quick Start

```bash
# Clone repository
git clone <repo-url>
cd millionx-mvp

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# Verify health
curl http://localhost:8000/health
curl http://localhost:3000/health
```

## 🏗️ Architecture

- **FastAPI**: Risk scoring engine
- **Node.js**: WhatsApp webhook handler
- **Redis**: Blacklist cache
- **PostgreSQL**: Transaction database (Supabase)

## 📱 Features

### COD Shield
- Real-time fraud detection
- 4-factor risk scoring
- <100ms response time

### Bhai-Bot
- WhatsApp-native interface
- Benglish support
- Profit tracking
- Inventory alerts

## 🧪 Testing

```bash
# FastAPI tests
cd fastapi-risk-engine
pytest -v

# WhatsApp bot tests
cd whatsapp-bot
npm test
```

## 📊 API Documentation

FastAPI Swagger: http://localhost:8000/docs

### Example: Risk Score API

**Endpoint:** `POST /api/v1/risk-score`

**Request:**
```json
{
  "order_id": "ORD-123",
  "customer_phone": "+8801712345678",
  "order_details": {
    "total_amount": 1500,
    "is_first_order": true
  }
}
```

**Response:**
```json
{
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "recommendation": "CONFIRMATION_CALL_REQUIRED"
}
```

## 🔧 Environment Variables

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# WhatsApp
WHATSAPP_TOKEN=xxx
VERIFY_TOKEN=your_secret
PHONE_NUMBER_ID=xxx
```

## 📝 Phase 1 Status

✅ COD Shield API  
✅ Risk scoring algorithm  
✅ WhatsApp webhook  
✅ Basic intent routing  
✅ Docker containerization  
✅ Test coverage >85%

## 🗺️ Roadmap

**Phase 2:** TrendSeq, Demand Forecasting  
**Phase 3:** Agentic Swarm, LangGraph Integration

## 📄 License

MIT

## 👥 Team

Built with ❤️ by the MillionX team
```

#### Deliverables:
- [ ] README.md created
- [ ] All sections complete
- [ ] Examples tested

---

### Task 4.3: Performance Benchmarking
**Owner:** QA/Backend  
**Duration:** 30 minutes  
**Priority:** P2

#### Steps:

Create `tests/benchmark.py`:
```python
import requests
import time
import statistics

BASE_URL = "http://localhost:8000"

def benchmark_risk_api(iterations=100):
    """Benchmark risk API performance"""
    response_times = []
    
    payload = {
        "order_id": "BENCH-001",
        "merchant_id": "MERCH-001",
        "customer_phone": "+8801700000000",
        "delivery_address": {
            "area": "Gulshan",
            "city": "Dhaka",
            "postal_code": "1212"
        },
        "order_details": {
            "total_amount": 500,
            "currency": "BDT",
            "items_count": 1,
            "is_first_order": False
        },
        "timestamp": "2025-12-13T10:00:00Z"
    }
    
    print(f"Running {iterations} requests...")
    
    for i in range(iterations):
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/risk-score", json=payload)
        end = time.time()
        
        if response.status_code == 200:
            response_times.append((end - start) * 1000)  # Convert to ms
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{iterations}")
    
    # Calculate statistics
    avg = statistics.mean(response_times)
    median = statistics.median(response_times)
    p95 = sorted(response_times)[int(len(response_times) * 0.95)]
    p99 = sorted(response_times)[int(len(response_times) * 0.99)]
    
    print("\n📊 Benchmark Results:")
    print(f"  Average: {avg:.2f}ms")
    print(f"  Median: {median:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    print(f"  Min: {min(response_times):.2f}ms")
    print(f"  Max: {max(response_times):.2f}ms")
    
    # Check against target
    if p95 < 100:
        print("\n✅ PASSED: P95 response time < 100ms")
    else:
        print(f"\n❌ FAILED: P95 response time ({p95:.2f}ms) exceeds 100ms target")

if __name__ == "__main__":
    benchmark_risk_api()
```

Run benchmark:
```bash
python tests/benchmark.py
```

#### Deliverables:
- [ ] Benchmark script created
- [ ] P95 response time < 100ms confirmed

#### Acceptance Criteria:
- Average response time < 50ms
- P95 < 100ms
- No timeouts or errors

---

## ✅ Final Checklist

### Core Functionality
- [ ] COD Shield API returns accurate risk scores
- [ ] All 4 risk factors implemented (blacklist, first order, address, time)
- [ ] WhatsApp webhook verifies successfully
- [ ] Bot responds to all 3 commands (profit, inventory, risk check)
- [ ] Redis blacklist cache working
- [ ] Supabase database tables created and populated

### Testing
- [ ] Unit tests passing (>85% coverage)
- [ ] Integration tests passing
- [ ] Manual E2E test completed
- [ ] Performance benchmark passed (P95 < 100ms)

### Deployment
- [ ] All Docker containers build successfully
- [ ] docker-compose up runs without errors
- [ ] Health checks return healthy status
- [ ] Environment variables configured
- [ ] Redis data persists across restarts

### Documentation
- [ ] README.md complete
- [ ] Demo script prepared
- [ ] API documentation accessible
- [ ] Code comments added

### Demo Readiness
- [ ] Demo rehearsed with team
- [ ] Test WhatsApp account configured
- [ ] Backup scenarios prepared
- [ ] Presentation slides (if needed)

---

## 📊 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| API Response Time (P95) | <100ms | ⏳ |
| Test Coverage | >85% | ⏳ |
| WhatsApp Message Success Rate | 100% | ⏳ |
| Risk Score Accuracy | >90% | ⏳ |
| Uptime During Demo | 100% | ⏳ |

---

## 🆘 Troubleshooting Guide

### Issue: Redis Connection Failed
```bash
# Check if Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Check logs
docker-compose logs redis
```

### Issue: WhatsApp Webhook Not Receiving Messages
1. Check webhook URL is HTTPS
2. Verify VERIFY_TOKEN matches Meta dashboard
3. Check ngrok tunnel is still active
4. Review webhook logs: `docker-compose logs whatsapp-bot`

### Issue: FastAPI Import Errors
```bash
# Rebuild container
docker-compose build fastapi

# Check Python version
docker-compose exec fastapi python --version

# Reinstall dependencies
docker-compose exec fastapi pip install -r requirements.txt
```

### Issue: Supabase Connection Timeout
1. Check Supabase project is not paused
2. Verify SUPABASE_URL in .env
3. Test connection: `curl https://your-project.supabase.co`

---

## 🎯 Next Steps After Phase 1

1. **Phase 2 Kickoff Meeting**
   - Review Phase 1 metrics
   - Plan TrendSeq implementation
   - Assign Phase 2 tasks

2. **Production Deployment**
   - Deploy to cloud provider
   - Setup CI/CD pipeline
   - Configure monitoring

3. **Merchant Onboarding**
   - Recruit 10 pilot merchants
   - Collect feedback
   - Iterate based on usage

---

**Document Version:** 1.0  
**Last Updated:** December 13, 2025  
**Status:** Ready for Implementation  

**Good luck with the implementation! 🚀**
