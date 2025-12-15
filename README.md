# MillionX MVP - Phase 1 Setup Guide

## 🎯 Day 0: Environment Setup ✅ COMPLETED
## 🎯 Day 1: FastAPI Risk Engine ✅ COMPLETED
## 🎯 Day 2: WhatsApp Bot (Bhai-Bot) ✅ COMPLETED

This guide documents the completed setup tasks for the MillionX MVP.

---

## ✅ Task 0.1: Initialize Project Structure - COMPLETED
## ✅ Task 0.2: Setup Supabase Project - COMPLETED
## ✅ Task 0.3: Setup Redis Instance - COMPLETED
## ✅ Task 0.4: WhatsApp Business API Setup - COMPLETED

Project structure has been created and all services are running:
```
millionx-mvp/
├── fastapi-risk-engine/    # FastAPI COD Shield API ✅
├── whatsapp-bot/           # WhatsApp webhook handler
├── shared/                 # Shared utilities
├── tests/                  # Integration tests
├── .gitignore             # Git ignore rules
├── .env.example           # Environment template
├── .env                   # Your actual credentials
└── README.md              # This file
```

**Services Status:**
- ✅ **Supabase:** Database configured and accessible
- ✅ **Redis:** Running locally on port 6379 (millionx-redis container)
- ✅ **WhatsApp API:** Business API configured with test credentials
- ✅ **FastAPI:** COD Shield API running on http://localhost:8000

---

## ✅ Day 1: FastAPI Risk Engine - COMPLETED

### What Was Built:
- **COD Shield API** with complete risk scoring algorithm
- **Redis integration** for blacklist management
- **Risk factors analysis** (phone blacklist, first order value, address risk, time anomalies)
- **Interactive API docs** at http://localhost:8000/docs
- **Health check endpoint** with Redis connectivity status

### API Endpoints Available:
- `GET /` - Service information
- `GET /health` - Health check with Redis status
- `POST /api/v1/risk-score` - Calculate order risk score
- `POST /api/v1/blacklist/add` - Add phone to blacklist
- `GET /api/v1/blacklist/check/{phone}` - Check blacklist status

### Risk Scoring Logic:
- **0-40:** LOW risk → Proceed with COD
- **41-70:** MEDIUM risk → Require confirmation call
- **71-100:** HIGH risk → Advance payment mandatory

---

## ✅ Day 2: WhatsApp Bot (DAYS 0, 1, 2 COMPLETE!

**Day 0, 1 & 2 Complete:** ✅ Environment, FastAPI Risk Engine, and WhatsApp Bot implemented

### What's Working:
- ✅ **COD Shield API** - Real-time fraud detection for COD orders
- ✅ **Bhai-Bot** - WhatsApp interface for merchants (natural language)
- ✅ **Redis Blacklist** - Phone number fraud tracking
- ✅ **Risk Scoring Algorithm** - Multi-factor risk assessment
- ✅ **Network Fraud Reporting** - Community-powered blacklist
- ✅ **API Documentation** - Interactive docs at http://localhost:8000/docs
- ✅ **Health Monitoring** - Service status for both APIs

### Running Services:
- 🚀 **FastAPI (COD Shield):** http://localhost:8000
- 🤖 **WhatsApp Bot (Bhai-Bot):** http://localhost:3000

### Next Steps:
Ready for **Day 3: Testing & Docker Deployment
- 🚨 **"report +880..."** - Report fraudster to network blacklist
- 📷 **Image upload** - Product cataloging (acknowledgment only in MVP)
- ❓ **Help** - Get list of available commands

### Bot Endpoints:
- `GET /webhook/whatsapp` - Webhook verification (for Meta)
- `POST /webhook/whatsapp` - Message handler
- `GET /health` - Health check
- `GET /` - Service information

### Features:
- ✅ Natural language processing (keyword matching)
- ✅ Real-time risk checking via COD Shield API
- ✅ Network effect fraud reporting
- ✅ Mock profit & inventory queries
- ✅ Image upload acknowledgment
- ✅ Bilingual support (English & Benglish)

**Server Status:** Running on http://localhost:3000 🚀

---

## 🎉 Phase 1 MVP Status: COMPLETE!

**Day 0 & Day 1 Complete:** ✅ Environment setup and FastAPI Risk Engine implemented

### What's Working:
- ✅ **COD Shield API** - Real-time fraud detection for COD orders
- ✅ **Redis Blacklist** - Phone number fraud tracking
- ✅ **Risk Scoring Algorithm** - Multi-factor risk assessment
- ✅ **API Documentation** - Interactive docs at http://localhost:8000/docs
- ✅ **Health Monitoring** - Service status and Redis connectivity

### Next Steps:
Ready for **Day 2: WhatsApp Bot Implementation** or **Day 3: Testing & Docker**

### Quick Start:
```bash
# Terminal 1: Start FastAPI server
cd fastapi-risk-engine
python main.py

# Terminal 2: Start WhatsApp Bot
cd whatsapp-bot
node index.js

# Access services
# - FastAPI Docs: http://localhost:8000/docs
# - WhatsApp Bot: http://localhost:3000
# - FastAPI Health: http://localhost:8000/health
# - Bot Health: http://localhost:3000/health

# Test risk scoring
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{"order_id":"TEST-001","merchant_id":"MERCH-001","customer_phone":"+8801700000000","delivery_address":{"area":"Gulshan","city":"Dhaka","postal_code":"1212"},"order_details":{"total_amount":500,"currency":"BDT","items_count":1,"is_first_order":false},"timestamp":"2025-12-15T10:00:00Z"}'
```

---

1. **Create Supabase Account & Project:**
   - Go to: https://supabase.com/dashboard
   - Click "New Project"
   - Fill in:
     - Project Name: `millionx-mvp`
     - Database Password: Generate a strong password (save it!)
     - Region: Select "Southeast Asia (Singapore)" or closest
   - Wait ~2 minutes for provisioning

2. **Get API Credentials:**
   - Navigate to: Settings → API
   - Copy these values:
     - **Project URL** (e.g., https://abc123.supabase.co)
     - **anon public key** (starts with "eyJ...")
     - **service_role secret key** (starts with "eyJ...")

3. **Save Credentials:**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and paste your Supabase credentials
   notepad .env
   ```

---

### Task 0.3: Setup Redis Instance (15 minutes)

**Option A: Local Docker (Recommended for Development)**

```bash
# Install Docker Desktop if not installed:
# Download from: https://www.docker.com/products/docker-desktop/

# Run Redis container
docker run -d --name millionx-redis -p 6379:6379 redis:7-alpine

# Verify it's running
docker ps
```

**Option B: Cloud Redis (For Production)**
- Use Upstash Free Tier: https://upstash.com/
- Or Redis Cloud: https://redis.com/try-free/

**Test Connection:**
```bash
# Install Redis CLI (if not installed)
# Windows: choco install redis
# Or download from: https://github.com/microsoftarchive/redis/releases

# Test connection
redis-cli ping
# Should return: PONG
```

---

### Task 0.4: WhatsApp Business API Setup (45 minutes)

1. **Create Meta Developer Account:**
   - Go to: https://developers.facebook.com/
   - Log in with Facebook account (create one if needed)
   - Complete developer registration

2. **Create New App:**
   - Click "Create App"
   - Select "Business" type
   - Fill in:
     - App Name: "MillionX MVP"
     - Contact Email: Your email

3. **Add WhatsApp Product:**
   - In your app dashboard, click "Add Product"
   - Find "WhatsApp" and click "Set Up"

4. **Get Started with WhatsApp:**
   - Navigate to: WhatsApp → Getting Started
   - You'll see a test phone number provided by Meta
   - Add your personal WhatsApp number to test recipients

5. **Generate Access Token:**
   - In the Getting Started section, you'll see a **temporary access token** (24 hours)
   - Copy this token (starts with "EAA...")
   - For production, you'll need to generate a permanent token later

6. **Get Phone Number ID:**
   - Still in Getting Started section
   - Look for "Phone Number ID" 
   - Copy this ID (numeric value)

7. **Test Sending a Message:**
   - Use the API test console to send yourself a test message
   - If you receive it, WhatsApp API is working! ✅

8. **Save Credentials to .env:**
   ```bash
   # Edit your .env file
   WHATSAPP_TOKEN=EAAxxxxxxxxxxxx
   PHONE_NUMBER_ID=123456789012345
   VERIFY_TOKEN=millionx_secure_token_123
   ```

   Note: `VERIFY_TOKEN` is any secret string you choose - we'll use it later for webhook verification.

---

### Task 0.5: Verify Environment Configuration

1. **Check your .env file has all required values:**
   ```bash
   cat .env
   ```

   Should contain:
   - ✅ SUPABASE_URL
   - ✅ SUPABASE_ANON_KEY
   - ✅ SUPABASE_SERVICE_KEY
   - ✅ REDIS_HOST
   - ✅ WHATSAPP_TOKEN
   - ✅ PHONE_NUMBER_ID
   - ✅ VERIFY_TOKEN

2. **Ensure .env is NOT committed to git:**
   ```bash
   git status
   # .env should NOT appear in untracked files
   ```

---

## 🎉 Day 0 Complete! 

Once all tasks are done, you're ready to start Day 1: FastAPI Development

### Quick Checklist:
- [ ] Project folders created
- [ ] Git repository initialized
- [ ] Supabase project created and credentials saved
- [ ] Redis running locally (or cloud URL saved)
- [ ] WhatsApp Business API configured
- [ ] All credentials in .env file
- [ ] .env file is in .gitignore

---

## 🆘 Need Help?

### Common Issues:

**Redis won't start:**
```bash
# Check if port 6379 is already in use
netstat -ano | findstr :6379

# Stop existing Redis container
docker stop millionx-redis
docker rm millionx-redis

# Start fresh
docker run -d --name millionx-redis -p 6379:6379 redis:7-alpine
```

**WhatsApp token expired:**
- Temporary tokens last 24 hours
- Generate a new one from Meta Developer Dashboard
- For production, set up a system user with permanent token

**Supabase connection fails:**
- Verify project is not paused (free tier pauses after inactivity)
- Check the URL format: `https://[project-id].supabase.co`
- Ensure you copied the correct keys (anon vs service_role)

---

## 📚 Reference Documents:
- Full Implementation Plan: `../phase1-implementation.md`
- Detailed Tasks: `../phase1-tasks.md`
- Proposal: `../proposal.txt`

---

## 🚀 Ready for Next Phase!

Your MillionX MVP has a working **COD Shield** fraud detection system. Next steps:

1. **Day 2:** Implement WhatsApp Bot for merchant interface
2. **Day 3:** Add comprehensive testing and Docker deployment
3. **Day 4:** Integration testing and demo preparation

**Current Status:** FastAPI Risk Engine operational and ready for integration! 🎯
