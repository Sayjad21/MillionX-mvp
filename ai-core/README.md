# AI Core - Phase 3 Implementation

## 🎯 Overview

This is the **Inventory Copilot** - the AI brain of MillionX that:

1. **Consumes** real-time sales data from Kafka
2. **Forecasts** future demand using NeuralProphet
3. **Advises** merchants using AI agents (LangGraph + optional LLM)

## 📦 Components

```
ai-core/
├── kafka_to_db.py          # Bridge: Kafka → Postgres
├── forecasting.py          # NeuralProphet demand forecasting
├── agent_workflow.py       # LangGraph agent orchestrator
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd G:\MillionX-mvp\ai-core
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env with your settings
notepad .env
```

**Required settings:**

- `DATABASE_URL` - Your Postgres/Supabase connection string
- `KAFKA_BOOTSTRAP_SERVERS` - Default: localhost:9092
- `OPENAI_API_KEY` - Optional (uses mock responses if not set)

### 3. Start the Bridge (Kafka → Database)

```powershell
# Terminal 1: Start syncing data from Kafka to Postgres
python kafka_to_db.py

# This will consume messages from:
# - source.market.shopify
# - source.market.daraz
# - source.social.tiktok
# - source.social.facebook

# Let it run for a few minutes to collect data
```

### 4. Generate Mock Data (if needed)

```powershell
# Terminal 2: Send test data to Kafka
cd ..\millionx-phase2
python mock_data_generator.py

# This creates:
# - 100 social posts
# - 50 e-commerce orders
# - 8 weather records
```

### 5. Test Forecasting

```powershell
# After 1-2 minutes of data collection, test forecasting

# Option A: Batch forecast (top 5 products)
python forecasting.py

# Option B: Forecast specific product
python forecasting.py PROD-123
```

**Expected output:**

```
🔮 DEMAND FORECASTING - TOP PRODUCTS
====================================================================

1. Samsung Galaxy S24
   Product ID: PROD-789
   Predicted Demand: 45 units (next 7 days)
   Avg Daily: 6.4 units/day
   Restock: ✅ YES
   Confidence: 85%
```

### 6. Run Agent Orchestrator

```powershell
# Option A: Batch mode (top 3 products)
python agent_workflow.py

# Option B: Single product with JSON output
python agent_workflow.py PROD-789
```

**Expected output:**

```
====================================================================
🚀 INVENTORY COPILOT - Analyzing PROD-789
====================================================================

📊 Analyst: Analyzing product PROD-789...
✅ Analyst: Forecast complete - 45 units predicted

💡 Advisor: Generating recommendation...
✅ Advisor: Demand for Samsung Galaxy S24 is rising!
   Predicted 45 units over 7 days. Restock now to avoid stockouts.

====================================================================
📊 FINAL RESULTS
====================================================================
Product: Samsung Galaxy S24
Predicted Demand: 45 units
Restock: ✅ YES

💡 Advice: Demand for Samsung Galaxy S24 is rising!
Predicted 45 units over 7 days. Restock now to avoid stockouts (confidence: 85%).
====================================================================
```

## 📊 Database Tables

The bridge creates these tables automatically:

### `sales_history` - Order data for forecasting

| Column           | Type     | Description                         |
| ---------------- | -------- | ----------------------------------- |
| order_id         | VARCHAR  | Unique order identifier             |
| product_id       | VARCHAR  | Product identifier                  |
| product_name     | VARCHAR  | Product name                        |
| product_category | VARCHAR  | Category (smartphone, laptop, etc.) |
| quantity         | INTEGER  | Units ordered                       |
| order_date       | DATETIME | When order was placed               |

### `social_signals` - Social media trends

| Column           | Type     | Description            |
| ---------------- | -------- | ---------------------- |
| post_id          | VARCHAR  | Unique post identifier |
| platform         | VARCHAR  | tiktok, facebook       |
| content          | TEXT     | Post content           |
| engagement_count | INTEGER  | Total engagement       |
| posted_at        | DATETIME | When posted            |

## 🧠 How It Works

### 1. Data Sync (kafka_to_db.py)

```
Kafka Topics              Postgres Tables
==================        ==================
source.market.shopify  →  sales_history
source.market.daraz    →  sales_history
source.social.tiktok   →  social_signals
source.social.facebook →  social_signals
```

### 2. Forecasting (forecasting.py)

```python
# Fetch last 60 days of sales
df = fetch_sales_history(product_id="PROD-123", days=60)

# Train NeuralProphet model
model = NeuralProphet(weekly_seasonality=True)
model.fit(df)

# Predict next 7 days
forecast = model.predict(future_dataframe)

# Recommendation logic
if predicted_demand > recent_avg * 1.5:
    restock_recommended = True
```

### 3. Agent Orchestration (agent_workflow.py)

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Analyst Agent      │  ← Runs DemandForecaster
│  - Fetch sales data │  ← Trains NeuralProphet
│  - Generate forecast│  ← Returns prediction
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Advisor Agent      │  ← Receives forecast
│  - Analyze numbers  │  ← Generates advice
│  - Create advice    │  ← Uses LLM or rules
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│     END     │  ← Returns advice to merchant
└─────────────┘
```

## 🎯 Integration with Phase 1 (FastAPI)

To integrate with your existing Phase 1 API:

```python
# In your FastAPI app (fastapi-risk-engine/main.py)

from ai_core.agent_workflow import InventoryCopilot

copilot = InventoryCopilot()

@app.get("/api/v1/inventory/forecast/{product_id}")
async def get_forecast(product_id: str):
    """Get demand forecast for a product"""
    result = copilot.run(product_id=product_id)

    return {
        "product_id": product_id,
        "predicted_demand": result['forecast_result']['predicted_demand'],
        "restock_recommended": result['forecast_result']['restock_recommended'],
        "advice": result['advice']
    }
```

## 🔧 Troubleshooting

### Issue: "Insufficient data" error

**Cause:** Not enough historical sales data (need 30+ days)

**Solution:**

```powershell
# Run mock data generator multiple times
cd ..\millionx-phase2
python mock_data_generator.py
python mock_data_generator.py
python mock_data_generator.py

# Wait 1-2 minutes for kafka_to_db.py to sync
```

### Issue: No OpenAI API key

**Solution:** The advisor uses mock responses automatically. No API key needed for testing!

### Issue: Database connection failed

**Solution:**

```powershell
# Check your DATABASE_URL in .env
# For Supabase, get it from: Project Settings → Database → Connection String

# Test connection:
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); print('✅ Connected!' if engine.connect() else '❌ Failed')"
```

### Issue: Kafka consumer not receiving messages

**Solution:**

```powershell
# 1. Check Kafka is running
docker ps | Select-String "kafka"

# 2. Check topics exist
docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092

# 3. Check messages in topics
docker exec millionx-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic source.market.shopify --from-beginning --max-messages 5
```

## 📈 Next Steps

1. **Connect to Phase 1 FastAPI** - Add forecast endpoints
2. **WhatsApp Integration** - Send restock alerts to merchants
3. **Dashboard** - Visualize forecasts in real-time
4. **Advanced Features**:
   - Category-level forecasting
   - Social sentiment impact
   - Weather correlation
   - Multi-product bundling

## 🎓 Learn More

- **NeuralProphet Docs**: https://neuralprophet.com
- **LangGraph Tutorial**: https://langchain-ai.github.io/langgraph
- **SQLAlchemy**: https://docs.sqlalchemy.org

---

**Made with ❤️ for MillionX Hackathon MVP**
