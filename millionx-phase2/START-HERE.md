# ✅ Your Setup is Ready!

## 🎉 What I Just Configured

### 1. Created `.env` File ✅
Location: `millionx-phase2/.env`

**Snowflake Settings (Pre-filled):**
- Account: `CZHFAZV-PZ79941` ✅
- User: `SAYJAD` ✅
- Database: `MILLIONX` ✅
- Role: `ACCOUNTADMIN` ✅

**What You Need to Add:**
- [ ] Your Snowflake password
- [ ] OpenWeatherMap API key

---

## 🚦 Next Steps (12 Minutes)

### Step 1: Add Your Password (1 min)
```powershell
# Open the .env file
cd C:\Users\Legion\OneDrive\Desktop\millionx\millionx-mvp\millionx-phase2
notepad .env

# Find line 5:
SNOWFLAKE_PASSWORD=YOUR_PASSWORD_HERE

# Replace with your actual Snowflake password
# Save and close
```

---

### Step 2: Get OpenWeather API Key (2 mins + 10 min wait)

**Which API to Use:** ✅ **Current Weather Data** (FREE)

**Don't worry about:**
- ❌ "One Call API 3.0" (that's paid)
- ❌ Professional collections (paid)
- ❌ Historical data (paid)

**What's FREE and perfect for us:**
- ✅ Current Weather Data
- ✅ 5 Day / 3 Hour Forecast
- ✅ Air Pollution API

#### Get Your Key:
```
1. Go to: https://home.openweathermap.org/users/sign_up
2. Sign up (takes 2 minutes)
3. Verify your email
4. Go to: https://home.openweathermap.org/api_keys
5. Copy the default API key (already created for you)
6. Paste it in .env file:
   OPENWEATHER_API_KEY=your_key_here
7. ⏰ Wait 10 minutes for activation (go get coffee!)
```

---

## 🧪 Step 3: Test Your Setup

### Test Snowflake (After adding password)
```powershell
cd millionx-phase2\snowflake

# Install dependencies
pip install snowflake-connector-python python-dotenv

# Test connection
python -c "import os; from dotenv import load_dotenv; import snowflake.connector; load_dotenv('../.env'); conn = snowflake.connector.connect(account=os.getenv('SNOWFLAKE_ACCOUNT'), user=os.getenv('SNOWFLAKE_USER'), password=os.getenv('SNOWFLAKE_PASSWORD'), role=os.getenv('SNOWFLAKE_ROLE')); print('✅ Snowflake connected!'); print(f'User: {conn.user}'); conn.close()"
```

**Expected:**
```
✅ Snowflake connected!
User: SAYJAD
```

---

### Test OpenWeather (After 10 min wait)
```powershell
# Replace YOUR_API_KEY with your actual key
curl "https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid=YOUR_API_KEY"
```

**Expected:** JSON with Dhaka weather data

**If error "Invalid API key":**
- Wait 10 more minutes (key still activating)
- Double-check you copied it correctly

---

## 📋 Complete Checklist

### Before Testing
- [ ] Password added to `.env` file
- [ ] OpenWeather account created
- [ ] API key copied to `.env` file
- [ ] Waited 10 minutes for API key activation
- [ ] Snowflake connection test passed
- [ ] OpenWeather API test passed
- [ ] Initialize Snowflake schema (see below)

---

## 🗄️ Step 4: Initialize Snowflake Database

### Using Web UI (Easiest):
```
1. Go to: https://app.snowflake.com
2. Login:
   - Account: CZHFAZV-PZ79941
   - User: SAYJAD
   - Password: (your password)

3. Click "Worksheets" (left sidebar)
4. Click "+" to create new worksheet
5. Open this file in a text editor:
   C:\Users\Legion\OneDrive\Desktop\millionx\millionx-mvp\millionx-phase2\snowflake\schema-setup.sql
   
6. Copy ALL the contents
7. Paste into Snowflake worksheet
8. Click "Run All" (top right, play button)
9. Wait 2-3 minutes

Expected output:
✓ Database MILLIONX created
✓ Schema RAW_DATA created
✓ Table SOCIAL_POSTS created
✓ Table MARKET_ORDERS created
✓ Table PRICE_HISTORY created
✓ Table WEATHER_LOGS created
✓ 15 indexes created
✓ 8 views created
```

---

## ✅ You're Ready When...

All these are checked:

- [ ] `.env` file has your password
- [ ] `.env` file has OpenWeather API key
- [ ] Snowflake connection test passed
- [ ] OpenWeather API test passed
- [ ] Snowflake database schema initialized (4 tables created)

---

## 🚀 Then Start Testing!

Open: [TESTING-QUICK-START.md](./TESTING-QUICK-START.md)

Follow the guide to:
1. Start all services
2. Send test data through pipeline
3. Verify data in Snowflake
4. Check Weaviate vectors
5. View Grafana dashboards

**Total testing time:** 30 minutes

---

## 📞 Quick Links

**Files You Need:**
- Config: [.env](file:///C:/Users/Legion/OneDrive/Desktop/millionx/millionx-mvp/millionx-phase2/.env)
- Schema: [schema-setup.sql](file:///C:/Users/Legion/OneDrive/Desktop/millionx/millionx-mvp/millionx-phase2/snowflake/schema-setup.sql)
- Testing: [TESTING-QUICK-START.md](./TESTING-QUICK-START.md)

**Your Snowflake:**
- Web UI: https://app.snowflake.com
- Account: CZHFAZV-PZ79941
- User: SAYJAD

**OpenWeather:**
- Sign Up: https://home.openweathermap.org/users/sign_up
- API Keys: https://home.openweathermap.org/api_keys
- **Use This API:** Current Weather Data (FREE)

**Dashboards (After services start):**
- Kafka UI: http://localhost:8080
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

---

## 💡 Summary

**What's Done:**
- ✅ Snowflake credentials configured
- ✅ .env file created with your account
- ✅ All connection settings ready

**What You Do:**
1. Add your Snowflake password to `.env` (1 min)
2. Get OpenWeather API key and add to `.env` (2 min)
3. Wait 10 minutes for API key activation ☕
4. Test both connections (2 min)
5. Initialize Snowflake database (3 min)
6. Start testing! (30 min)

**Total Time:** ~45 minutes

---

**Status:** Configured ✅ | Waiting for: Your password + API key  
**Next:** [SETUP-INSTRUCTIONS.md](./SETUP-INSTRUCTIONS.md) for detailed steps
