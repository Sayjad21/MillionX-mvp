# OpenWeatherMap Setup Guide 🌤️

## Overview
OpenWeatherMap provides free weather data for up to 1,000,000 API calls per month - more than enough for MillionX's hourly fetches.

**Free Tier Features:**
- ✅ Current weather data
- ✅ 60 calls/minute
- ✅ 1,000,000 calls/month
- ✅ Access to 8 Bangladesh cities

**Monthly Usage:**
- 8 cities × 24 hours × 30 days = **5,760 calls/month** (well within free tier)

---

## Step 1: Sign Up (2 minutes)

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Click **"Sign Up"** (top right)
3. Fill in your details:
   - Email
   - Username
   - Password
4. Verify your email address

---

## Step 2: Get API Key (1 minute)

1. Log in to your account
2. Go to **"API keys"** tab
3. Copy the default API key (or create a new one)
4. Save it securely

**Example API Key:**
```
abcd1234efgh5678ijkl9012mnop3456
```

---

## Step 3: Configure MillionX (2 minutes)

### Option A: Add to .env file (Recommended)

Edit `millionx-phase2/.env`:

```bash
# OpenWeatherMap Configuration
OPENWEATHER_API_KEY=your_api_key_here
KAFKA_WEATHER_TOPIC=context.weather
```

### Option B: Export as environment variable

```bash
# Linux/Mac
export OPENWEATHER_API_KEY="your_api_key_here"

# Windows PowerShell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

---

## Step 4: Test Weather Fetcher (2 minutes)

### Manual Test

```bash
cd millionx-phase2/weather-fetcher
python weather_fetcher.py
```

**Expected Output:**
```
2025-12-24 14:00:00 - Weather data fetched successfully
Dhaka: 28°C, Clear sky
Chittagong: 26°C, Few clouds
Sylhet: 25°C, Light rain
...
✅ Published 8 weather records to Kafka
```

### Verify in Kafka

```bash
# Check if weather data is in Kafka
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic context.weather \
  --from-beginning \
  --max-messages 5
```

---

## Step 5: Schedule Hourly Fetches (Optional)

### Option A: Kubernetes CronJob (Production)

File already exists: `millionx-phase2/weather-fetcher/k8s-cronjob.yaml`

```bash
kubectl apply -f millionx-phase2/weather-fetcher/k8s-cronjob.yaml
```

### Option B: Linux cron

```bash
# Edit crontab
crontab -e

# Add hourly fetch (runs at minute 0 of every hour)
0 * * * * cd /path/to/millionx-phase2/weather-fetcher && python weather_fetcher.py
```

### Option C: Windows Task Scheduler

1. Open **Task Scheduler**
2. Create **Basic Task**:
   - Name: "MillionX Weather Fetch"
   - Trigger: Daily, repeat every 1 hour
   - Action: Start a program
     - Program: `python`
     - Arguments: `C:\path\to\millionx-phase2\weather-fetcher\weather_fetcher.py`
     - Start in: `C:\path\to\millionx-phase2\weather-fetcher`

### Option D: Manual Execution (Development)

Just run manually when needed:

```bash
python weather_fetcher.py
```

---

## API Usage Monitoring

### Check Your Usage

1. Log in to [OpenWeatherMap Dashboard](https://home.openweathermap.org/api_keys)
2. Go to **"Statistics"** tab
3. View hourly/daily API calls

**Free Tier Limits:**
- ⚠️ If you exceed 60 calls/minute, requests will be rate-limited
- ⚠️ If you exceed 1,000,000 calls/month, API will stop working

**Current MillionX Usage:**
- 8 calls/hour = 192 calls/day = 5,760 calls/month
- **Safe:** Using only 0.6% of free tier!

---

## Weather Data Format

The weather fetcher sends data to Kafka in this format:

```json
{
  "city": "Dhaka",
  "country": "BD",
  "latitude": 23.8103,
  "longitude": 90.4125,
  "timestamp": "2025-12-24T14:00:00Z",
  "weather": {
    "main": "Clear",
    "description": "clear sky",
    "icon": "01d"
  },
  "temperature": {
    "current": 28.5,
    "feels_like": 30.2,
    "min": 26.0,
    "max": 31.0
  },
  "humidity": 65,
  "pressure": 1013,
  "wind": {
    "speed": 3.5,
    "direction": 120
  },
  "visibility": 10000,
  "clouds": 10
}
```

---

## Integration Points

Weather data is used in the following pipeline components:

### 1. Context Enricher (`stream-processors/context_enricher.py`)
- Adds weather context to social posts
- Correlates product mentions with weather
- Example: "Raincoat sales spike during monsoon"

### 2. Forecasting Engine (`ai-core/forecasting.py`)
- Can be extended to include weather as a feature
- Example: "Demand for umbrellas increases when rain is forecasted"

### 3. TimescaleDB Analytics
- Weather data stored in hypertable: `weather_history`
- Query example:
  ```sql
  SELECT 
    city,
    AVG(temperature) as avg_temp,
    COUNT(*) as observations
  FROM weather_history
  WHERE time > NOW() - INTERVAL '7 days'
  GROUP BY city;
  ```

---

## Troubleshooting

### Error: "Invalid API key"

**Problem:** API key not recognized

**Solution:**
1. Check API key is correct (no extra spaces)
2. Wait 10 minutes after creating key (activation delay)
3. Verify key is activated in OpenWeatherMap dashboard

---

### Error: "429 Too Many Requests"

**Problem:** Exceeded rate limit (60 calls/minute)

**Solution:**
1. Add delay between API calls in code:
   ```python
   time.sleep(1)  # 1 second between calls
   ```
2. Check if script is running multiple times simultaneously

---

### Error: "401 Unauthorized"

**Problem:** API key not found in environment

**Solution:**
1. Verify `.env` file exists in `millionx-phase2/` directory
2. Check environment variable is loaded:
   ```bash
   echo $OPENWEATHER_API_KEY
   ```
3. Restart the script after setting environment variable

---

### No data in Kafka

**Problem:** Weather fetcher runs but no data in Kafka topic

**Solution:**
1. Check Kafka is running:
   ```bash
   docker-compose ps kafka
   ```
2. Check topic exists:
   ```bash
   kafka-topics.sh --list --bootstrap-server localhost:9092
   ```
3. Check weather fetcher logs for errors:
   ```bash
   tail -f weather_fetcher.log
   ```

---

## Cost Savings

| Feature | Paid Alternative | OpenWeatherMap Free | Savings |
|---------|------------------|---------------------|---------|
| Weather API | AWS Weather API | Free | $50/month |
| Historical Data | AccuWeather | Free (current) | $100/month |
| Forecasting | WeatherStack | Free (current) | $30/month |
| **TOTAL** | **$180/month** | **$0/month** | **$180/month** |

**Annual Savings:** $2,160/year 🎉

---

## Best Practices

### 1. Cache Weather Data
- Weather doesn't change every second
- Cache for 1 hour to reduce API calls
- Store in Redis for fast access

### 2. Handle API Errors Gracefully
```python
try:
    weather = fetch_weather(city)
except requests.exceptions.RequestException:
    # Use last known weather or skip
    logger.warning(f"Failed to fetch weather for {city}")
```

### 3. Monitor API Usage
- Set up alerts if usage > 80% of limit
- Log all API calls for debugging
- Track which cities consume most calls

### 4. Batch Multiple Cities
- Fetch all 8 cities in one run
- Don't run separate scripts per city
- Current implementation already batches

---

## Alternative: Mock Weather Data (No API)

If you don't want to use OpenWeatherMap, use mock data:

```python
# In weather_fetcher.py, replace API call with:
def fetch_mock_weather(city):
    """Generate realistic mock weather data"""
    return {
        "city": city,
        "temperature": random.randint(20, 35),
        "humidity": random.randint(50, 90),
        "conditions": random.choice(['Clear', 'Clouds', 'Rain']),
        "timestamp": datetime.now().isoformat()
    }
```

**When to use mock data:**
- Development/testing
- Don't want to create API account
- Offline development

---

## Next Steps

✅ **Phase 3 Complete!** Weather integration is ready.

**Continue with:**
- [ ] Test enhanced mock data generator (Step 3.1)
- [ ] Validate seasonal patterns in forecasting
- [ ] Check TimescaleDB weather storage
- [ ] Run full pipeline test

---

**Setup Time:** ~10 minutes  
**Monthly Cost:** $0 (FREE)  
**API Calls Needed:** 5,760/month (0.6% of limit)

🌤️ **Weather data ready for context enrichment!**
