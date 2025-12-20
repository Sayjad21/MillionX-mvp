# Setup Instructions - Your Snowflake is Configured! ✅

## ✅ What's Already Done

Your Snowflake credentials are configured in `.env` file:
- **Account:** CZHFAZV-PZ79941 ✅
- **User:** SAYJAD ✅
- **URL:** CZHFAZV-PZ79941.snowflakecomputing.com ✅
- **Role:** ACCOUNTADMIN ✅

---

## ⚠️ Required: Complete These 2 Steps

### Step 1: Add Your Snowflake Password (1 minute)

```bash
# Open .env file
cd millionx-phase2
notepad .env

# Find this line:
SNOWFLAKE_PASSWORD=YOUR_PASSWORD_HERE

# Replace with your actual password:
SNOWFLAKE_PASSWORD=your_actual_password

# Save and close
```

---

### Step 2: Get OpenWeatherMap API Key (12 minutes)

#### A. Sign Up (2 minutes)
```
1. Go to: https://home.openweathermap.org/users/sign_up
2. Fill the form:
   - Email: your_email@example.com
   - Password: (create one)
3. Verify your email
```

#### B. Get API Key (1 minute)
```
1. Login to: https://home.openweathermap.org
2. Go to: https://home.openweathermap.org/api_keys
3. You'll see a default API key already created
4. Click "Copy" next to the API key
5. Should look like: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

#### C. Add to .env (1 minute)
```bash
# Open .env file
notepad .env

# Find this line:
OPENWEATHER_API_KEY=PASTE_YOUR_API_KEY_HERE

# Replace with your API key:
OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Save and close
```

#### D. Wait for Activation (10 minutes)
⚠️ **IMPORTANT:** New API keys take 10 minutes to activate. Get coffee! ☕

---

## 🧪 Step 3: Test Your Credentials

### Test Snowflake Connection
```powershell
cd millionx-phase2\snowflake

# Install dependencies (if not already)
pip install snowflake-connector-python python-dotenv

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
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    print('✅ Snowflake connection successful!')
    print(f'Connected as: {conn.user}')
    print(f'Account: {conn.account}')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

**Expected output:**
```
✅ Snowflake connection successful!
Connected as: SAYJAD
Account: CZHFAZV-PZ79941
```

---

### Test OpenWeatherMap API
```powershell
# Load .env (PowerShell)
$env:OPENWEATHER_API_KEY = (Get-Content .env | Select-String "OPENWEATHER_API_KEY").ToString().Split("=")[1]

# Test API call for Dhaka
curl "https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid=$env:OPENWEATHER_API_KEY"
```

**Expected output (JSON):**
```json
{
  "weather": [{"main": "Clear", "description": "clear sky"}],
  "main": {"temp": 301.5, "humidity": 65},
  "name": "Dhaka"
}
```

**If you get error "Invalid API key":**
- Wait 10 more minutes (key is still activating)
- Double-check you copied the key correctly
- Make sure you verified your email

---

## 🎯 Step 4: Initialize Snowflake Database

Once your Snowflake password is in `.env`, initialize the database:

### Option A: Using Snowflake Web UI (Easier)
```
1. Go to: https://app.snowflake.com
2. Login with:
   - Account: CZHFAZV-PZ79941
   - Username: SAYJAD
   - Password: (your password)
3. Click "Worksheets" in left menu
4. Click "+" to create new worksheet
5. Open file: millionx-phase2/snowflake/schema-setup.sql
6. Copy ALL contents and paste into worksheet
7. Click "Run All" (top right)
8. Wait 2-3 minutes
9. You should see:
   ✓ Database MILLIONX created
   ✓ Schema RAW_DATA created
   ✓ 4 tables created
   ✓ 15 indexes created
   ✓ 8 views created
```

### Option B: Using Python Script (Alternative)
```powershell
cd millionx-phase2\snowflake

python -c "
import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv('../.env')

# Read schema file
with open('schema-setup.sql', 'r') as f:
    sql_commands = f.read().split(';')

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE')
)

cursor = conn.cursor()

# Execute each command
for cmd in sql_commands:
    if cmd.strip():
        try:
            cursor.execute(cmd)
            print(f'✓ Executed: {cmd[:50]}...')
        except Exception as e:
            print(f'Error: {e}')

cursor.close()
conn.close()
print('\n✅ Snowflake schema initialized!')
"
```

---

## ✅ Verification Checklist

Before moving to testing, verify:

- [x] **Snowflake account exists** (Enterprise edition on AWS)
- [ ] **Snowflake password added to .env**
- [ ] **OpenWeather account created**
- [ ] **OpenWeather API key copied to .env**
- [ ] **Waited 10 minutes for API key activation**
- [ ] **Snowflake connection test passed**
- [ ] **OpenWeather API test passed**
- [ ] **Snowflake database schema initialized**

---

## 🚀 Next Steps

Once all checkboxes are ✅:

```
1. Go to: TESTING-QUICK-START.md
2. Run end-to-end pipeline test
3. Verify data flows through system
4. Check Grafana dashboards
```

---

## 📞 Quick Reference

**Your Snowflake Details:**
- Account: CZHFAZV-PZ79941
- User: SAYJAD
- URL: https://CZHFAZV-PZ79941.snowflakecomputing.com
- Web UI: https://app.snowflake.com
- Edition: Enterprise (AWS)

**OpenWeatherMap:**
- Sign Up: https://home.openweathermap.org/users/sign_up
- API Keys: https://home.openweathermap.org/api_keys
- API Docs: https://openweathermap.org/api
- **Use:** Current Weather Data API (FREE)
- **Don't Use:** One Call API 3.0 (paid)

**Files:**
- Config: `millionx-phase2/.env`
- Schema: `millionx-phase2/snowflake/schema-setup.sql`
- Testing Guide: `millionx-phase2/TESTING-QUICK-START.md`

---

## 🆘 Troubleshooting

### "Snowflake authentication failed"
```
- Check password in .env (no spaces, quotes, or special characters issues)
- Try logging in to Snowflake web UI to verify password works
- Make sure SNOWFLAKE_ACCOUNT matches: CZHFAZV-PZ79941
```

### "OpenWeather API returns 401"
```
- API key needs 10 minutes to activate after signup
- Check if key is correctly copied (no extra spaces)
- Verify email was confirmed
- Try again in a few minutes
```

### "Cannot find .env file"
```powershell
# Check current directory
pwd

# Should be in: C:\Users\Legion\OneDrive\Desktop\millionx\millionx-mvp\millionx-phase2

# If not, navigate there:
cd C:\Users\Legion\OneDrive\Desktop\millionx\millionx-mvp\millionx-phase2
```

---

**Status:** Snowflake configured ✅ | OpenWeather pending ⏳  
**Time Remaining:** 12 minutes (get API key + wait for activation)  
**Next:** [TESTING-QUICK-START.md](./TESTING-QUICK-START.md)
