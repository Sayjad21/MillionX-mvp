# Phase 2 Credentials & Setup Checklist

## 🎯 Quick Status

**Phase 2 Implementation:** ✅ COMPLETE  
**Ready for Testing:** ⚠️ Needs 2 credentials (see below)

---

## 📋 Required Credentials for Testing

### ✅ REQUIRED (Must Have - Both Free!)

#### 1. Snowflake Account
- **Purpose:** Store structured data (orders, social posts, price history)
- **Cost:** FREE (30-day trial, no credit card for trial)
- **Signup:** https://signup.snowflake.com
- **Time:** 5 minutes to setup
- **What you'll get:**
  ```
  SNOWFLAKE_ACCOUNT=<account>.<region>
  SNOWFLAKE_USER=<your_email>
  SNOWFLAKE_PASSWORD=<your_password>
  ```

#### 2. OpenWeatherMap API Key
- **Purpose:** Fetch real-time weather data for Bangladesh cities
- **Cost:** FREE (60 calls/min, 1M calls/month)
- **Signup:** https://openweathermap.org/api
- **Time:** 2 minutes (wait 10 min for API key activation)
- **What you'll get:**
  ```
  OPENWEATHER_API_KEY=abcd1234xyz5678
  ```

---

## 📋 Optional Credentials (Can Skip for Initial Testing)

### ⚪ For Real Social Media Scraping

#### 3. Proxy Service (BrightData/Smartproxy)
- **Purpose:** Rotate IPs to avoid TikTok/Facebook blocking
- **Cost:** $500-1000/month
- **Signup:** https://brightdata.com or https://smartproxy.com
- **Can Skip:** Yes, use sample data or Apify alternative
- **What you'll get:**
  ```
  PROXY_LIST=http://user:pass@proxy:port
  ```

#### 4. Facebook Graph API Token
- **Purpose:** Scrape Facebook posts via official API
- **Cost:** FREE
- **Signup:** https://developers.facebook.com
- **Can Skip:** Yes, focus on other data sources first
- **What you'll get:**
  ```
  FACEBOOK_ACCESS_TOKEN=EAAxxxx...
  ```

#### 5. TikTok API (Apify Alternative)
- **Purpose:** Scrape TikTok without maintaining scrapers
- **Cost:** $50-200/month
- **Signup:** https://apify.com
- **Can Skip:** Yes, not critical for MVP
- **What you'll get:**
  ```
  APIFY_TOKEN=apify_api_xyz123
  ```

---

## 📋 Optional Credentials (E-commerce Integration)

### ⚪ For Real E-commerce Data

#### 6. Shopify API Token
- **Purpose:** Sync orders from Shopify stores
- **Cost:** FREE (requires Shopify store)
- **Signup:** Create private app in Shopify admin
- **Can Skip:** Yes, unless you have a Shopify store
- **What you'll get:**
  ```
  SHOPIFY_SHOP_URL=your-store.myshopify.com
  SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
  ```

#### 7. Daraz API Credentials
- **Purpose:** Sync orders from Daraz marketplace
- **Cost:** FREE (requires Daraz seller account)
- **Signup:** https://sellercenter.daraz.com.bd
- **Can Skip:** Yes, unless you're a Daraz merchant
- **What you'll get:**
  ```
  DARAZ_APP_KEY=your_app_key
  DARAZ_APP_SECRET=your_app_secret
  ```

---

## 🚀 Quick Setup Instructions

### Step 1: Get Required Credentials (15 mins)

#### A. Snowflake
```bash
1. Go to https://signup.snowflake.com
2. Fill form:
   - Email: <your_email>
   - Snowflake Edition: Standard
   - Cloud Provider: AWS
   - Region: ap-southeast-1 (Singapore) or us-east-1
3. Verify email
4. Login to https://<account>.<region>.snowflakecomputing.com
5. Note your credentials

✅ You now have: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD
```

#### B. OpenWeatherMap
```bash
1. Go to https://openweathermap.org/api
2. Click "Sign Up" (top right)
3. Fill form and verify email
4. Login and go to "API Keys" tab
5. Copy default API key
6. ⚠️ IMPORTANT: Wait 10 minutes for key activation

✅ You now have: OPENWEATHER_API_KEY
```

---

### Step 2: Configure Environment File

```bash
cd millionx-phase2

# Create .env file
cat > .env << EOF
# ========================================
# REQUIRED CREDENTIALS (Fill these in!)
# ========================================

# Snowflake (from Step 1A)
SNOWFLAKE_ACCOUNT=<paste_here>      # Example: xy12345.ap-southeast-1
SNOWFLAKE_USER=<paste_here>          # Example: your_email@gmail.com
SNOWFLAKE_PASSWORD=<paste_here>      # Your Snowflake password
SNOWFLAKE_DATABASE=MILLIONX
SNOWFLAKE_SCHEMA=RAW_DATA
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# OpenWeatherMap (from Step 1B)
OPENWEATHER_API_KEY=<paste_here>     # Example: abcd1234xyz5678

# ========================================
# PRE-CONFIGURED (No changes needed)
# ========================================

# Kafka (already running from Week 1)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Privacy Salt (testing only - change in production!)
PRIVACY_SALT=testing_salt_2025_DO_NOT_USE_IN_PROD

# Redis (for context enricher)
REDIS_HOST=localhost
REDIS_PORT=6379

# Weaviate
WEAVIATE_URL=http://localhost:8082

# Batch Loading
BATCH_SIZE=1000
FLUSH_INTERVAL_SECONDS=60

# ========================================
# OPTIONAL (Leave commented for now)
# ========================================

# Proxy for web scraping
# PROXY_LIST=http://user:pass@proxy1:8080,http://user:pass@proxy2:8080

# Social Media APIs
# FACEBOOK_ACCESS_TOKEN=EAAxxxx...
# APIFY_TOKEN=apify_api_xyz123

# E-commerce APIs
# SHOPIFY_SHOP_URL=your-store.myshopify.com
# SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
# DARAZ_APP_KEY=your_key
# DARAZ_APP_SECRET=your_secret

EOF

echo "✅ .env file created!"
echo "⚠️  IMPORTANT: Fill in SNOWFLAKE_* and OPENWEATHER_API_KEY values"
```

---

### Step 3: Verify Credentials Work

#### Test Snowflake Connection
```bash
cd millionx-phase2/snowflake

# Install dependencies (if not already)
pip install snowflake-connector-python

# Test connection
python -c "
import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv('../.env')

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD')
    )
    print('✅ Snowflake connection successful!')
    print(f'Connected as: {conn.user}')
    conn.close()
except Exception as e:
    print(f'❌ Snowflake connection failed: {e}')
"
```

#### Test OpenWeatherMap API
```bash
cd millionx-phase2

# Load .env
source .env  # On Windows: use 'set' commands or load manually

# Test API call
curl "https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid=$OPENWEATHER_API_KEY"

# Expected: JSON response with weather data
# If error "Invalid API key": Wait 10 more minutes, key is still activating
```

---

## ✅ Checklist Before Testing

- [ ] **Snowflake account created** (5 mins)
- [ ] **OpenWeather API key obtained** (2 mins + 10 min wait)
- [ ] **`.env` file created in millionx-phase2/** (1 min)
- [ ] **SNOWFLAKE_ACCOUNT filled in .env** (copy-paste)
- [ ] **SNOWFLAKE_USER filled in .env** (copy-paste)
- [ ] **SNOWFLAKE_PASSWORD filled in .env** (copy-paste)
- [ ] **OPENWEATHER_API_KEY filled in .env** (copy-paste)
- [ ] **Snowflake connection test passed** (run script above)
- [ ] **OpenWeather API test passed** (run curl command above)

**When all checked:** You're ready! → Go to [TESTING-QUICK-START.md](./TESTING-QUICK-START.md)

---

## 🔐 Security Notes

### ⚠️ IMPORTANT: Keep .env file secure!

```bash
# Verify .env is in .gitignore
cat ../.gitignore | grep .env

# If not there, add it:
echo ".env" >> ../.gitignore
echo "*.env" >> ../.gitignore

# NEVER commit .env to git!
```

### 🔒 Production Deployment

When moving to production, use proper secret management:

```bash
# Kubernetes Secrets (recommended)
kubectl create secret generic millionx-credentials \
  --from-literal=snowflake-password=$SNOWFLAKE_PASSWORD \
  --from-literal=openweather-api-key=$OPENWEATHER_API_KEY

# Or use AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
```

---

## 📊 Cost Breakdown

| Service | Free Tier | Paid Tier | Monthly Cost |
|---------|-----------|-----------|--------------|
| **Snowflake** | 30-day trial ($400 credits) | Pay-as-you-go | $5-15 (optimized) |
| **OpenWeather** | 60 calls/min, 1M calls/month | N/A | $0 (free tier sufficient) |
| **BrightData Proxies** | N/A | Residential proxies | $500-1000 (optional) |
| **Apify** | $5 free credits | Pay-as-you-go | $50-200 (optional) |
| **Kafka** | Self-hosted | Confluent Cloud | $0 (self-hosted) |
| **Weaviate** | Self-hosted | Weaviate Cloud | $0 (self-hosted) |

**Total for Testing:** $0 (all free tiers)  
**Total for Production (minimal):** $5-15/month (just Snowflake, after trial)  
**Total for Full Production:** $555-1215/month (with proxies + Apify)

---

## 🆘 Getting Help

### Common Issues

**"Snowflake authentication failed"**
- Double-check account format: `<account>.<region>` (no https://)
- Verify you can login to web UI with same credentials
- Check for typos in .env file

**"OpenWeather returns 401 Unauthorized"**
- API key needs 10 minutes to activate after signup
- Check if you're using correct API key (not email!)
- Verify key in web UI: https://home.openweathermap.org/api_keys

**"Snowflake trial expired"**
- Trial is 30 days or $400 credits, whichever comes first
- With our optimized setup, $400 should last 25-30 days
- Can upgrade to paid plan (~$5-15/month with our optimizations)

**"Can't afford proxies/Apify"**
- Skip social media scraping for now
- Focus on Shopify/Daraz integrations (direct API, free)
- Or use synthetic/sample data for testing
- Real scraping can be added later

---

## 📞 Quick Reference

**Documentation:**
- Full Phase 2 Plan: [phase2-implementation.md](../phase2-implementation.md)
- Testing Guide: [TESTING-QUICK-START.md](./TESTING-QUICK-START.md)
- Week 4 Deployment: [WEEK4-DEPLOYMENT-GUIDE.md](./WEEK4-DEPLOYMENT-GUIDE.md)

**Signup Links:**
- Snowflake: https://signup.snowflake.com
- OpenWeather: https://openweathermap.org/api
- BrightData: https://brightdata.com
- Apify: https://apify.com
- Shopify Developers: https://developers.shopify.com
- Daraz Seller Center: https://sellercenter.daraz.com.bd

**Support:**
- Snowflake Docs: https://docs.snowflake.com
- OpenWeather Docs: https://openweathermap.org/api/one-call-3
- Kafka Docs: https://kafka.apache.org/documentation

---

**Last Updated:** December 20, 2025  
**Status:** Ready for credential setup  
**Time to Complete:** 15 minutes for required credentials
