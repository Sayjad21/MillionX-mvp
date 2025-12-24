<div align="center">

# 🧠 MillionX AI Core

### Intelligent Commerce Engine for South Asian SMEs

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

**Demand Forecasting • Dynamic Pricing • Monte Carlo Negotiation • Graph Analytics**

[Getting Started](#-quick-start) •
[Architecture](#-architecture) •
[API Reference](#-api-reference) •
[Configuration](#-configuration)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Module Reference](#-module-reference)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Integration Guide](#-integration-guide)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The **AI Core** is the intelligence engine powering the MillionX Commerce Platform. It provides South Asian SME merchants with enterprise-grade AI capabilities at zero infrastructure cost, replacing expensive cloud ML services with optimized open-source alternatives.

### Key Capabilities

| Capability | Description | Technology |
|------------|-------------|------------|
| **Demand Forecasting** | 7-day stockout prediction with seasonal patterns | AutoARIMA/AutoETS |
| **Dynamic Pricing** | Elasticity-based optimal price calculation | PriceShift Engine |
| **Negotiation AI** | Monte Carlo simulation with 4 customer archetypes | Haggling Twin |
| **Sentiment Analysis** | Real-time text polarity scoring | VADER |
| **Graph Analytics** | Co-purchase patterns and bundle recommendations | NetworkX |

### Cost Savings

```
┌─────────────────────────────────────────────────────────────────┐
│  CLOUD ALTERNATIVE          MONTHLY COST    OUR SOLUTION       │
├─────────────────────────────────────────────────────────────────┤
│  AWS SageMaker              $400+           statsforecast      │
│  Google Vertex AI           $300+           scikit-learn       │
│  Neo4j Aura                 $65+            NetworkX           │
│  OpenAI GPT-4               $200+           VADER + Rules      │
├─────────────────────────────────────────────────────────────────┤
│  TOTAL SAVINGS:             $965/month      $0 (self-hosted)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🔮 Demand Forecasting
- **7-day ahead predictions** with confidence intervals
- **Seasonal pattern recognition**: Eid, Pohela Boishakh, Monsoon, Winter
- **Regional variations**: Dhaka, Chittagong, Sylhet market patterns
- **Restock recommendations** with urgency levels

### 💰 PriceShift Engine
- **Price elasticity calculation** from historical sales data
- **Competitor price indexing** (simulated for MVP, ready for API integration)
- **Time-based surge pricing** with ethical guardrails
- **Three strategies**: Aggressive, Balanced, Conservative

### 🤝 Haggling Twin (Monte Carlo Simulation)
- **1,000 negotiation simulations** per request
- **4 customer archetypes** with weighted distribution:
  - Price Sensitive (40%) - Max 15% discount tolerance
  - Quality Focused (30%) - Willing to pay premium
  - Bargain Hunter (20%) - Expects 20%+ discounts
  - Impulse Buyer (10%) - Low price sensitivity
- **Conversion rate prediction** with confidence scores
- **Natural language counter-offers** in conversational tone

### 📊 Graph Analytics
- **Co-purchase network** built from order history
- **Centrality metrics**: PageRank, Betweenness, Degree
- **Bundle recommendations** with purchase frequency
- **Product importance scoring** for inventory prioritization

### 💬 Sentiment Analysis
- **VADER polarity scoring** (-1 to +1 compound score)
- **Batch processing support** for multiple texts
- **Label classification**: Positive, Negative, Neutral
- **Zero API cost** - runs entirely on CPU

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI CORE ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Kafka     │───▶│ kafka_to_db │───▶│  PostgreSQL │◀───│  FastAPI    │  │
│  │  Streams    │    │   Bridge    │    │  Database   │    │  Endpoints  │  │
│  └─────────────┘    └─────────────┘    └──────┬──────┘    └──────┬──────┘  │
│                                               │                   │         │
│                     ┌─────────────────────────┼───────────────────┘         │
│                     │                         │                             │
│                     ▼                         ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        AI MODULE LAYER                               │   │
│  ├──────────────┬──────────────┬──────────────┬──────────────┬─────────┤   │
│  │ forecasting  │ haggling_    │ graph_       │ sentiment    │ agent_  │   │
│  │ .py          │ engine.py    │ analytics.py │ .py          │ workflow│   │
│  ├──────────────┼──────────────┼──────────────┼──────────────┼─────────┤   │
│  │ • AutoARIMA  │ • PriceShift │ • PageRank   │ • VADER      │ • Copilot│  │
│  │ • AutoETS    │ • Monte Carlo│ • Betweenness│ • Polarity   │ • Advisor│  │
│  │ • Seasonality│ • Counter-   │ • Bundles    │ • Batch      │ • Rules  │  │
│  │ • Restock    │   Offers     │ • Community  │              │          │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┴─────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Shopify    │────▶│              │────▶│              │────▶│   FastAPI    │
│   Daraz      │     │    Kafka     │     │  PostgreSQL  │     │   Response   │
│   Social     │     │   Broker     │     │  TimescaleDB │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     INPUT              STREAMING            STORAGE              OUTPUT
```

---

## 📦 Module Reference

```
ai-core/
├── 📄 forecasting.py          # Demand prediction engine (AutoARIMA/AutoETS)
├── 📄 haggling_engine.py      # PriceShift + Haggling Twin (750 lines)
├── 📄 graph_analytics.py      # NetworkX graph analysis (310 lines)
├── 📄 sentiment.py            # VADER sentiment scoring (135 lines)
├── 📄 agent_workflow.py       # Inventory Copilot orchestrator
├── 📄 kafka_to_db.py          # Kafka → PostgreSQL bridge
├── 📄 requirements.txt        # Python dependencies
├── 📄 Dockerfile              # Container definition
├── 📄 .env.example            # Environment template
└── 📄 README.md               # This documentation
```

### Module Details

| Module | Lines | Purpose | Key Classes/Functions |
|--------|-------|---------|----------------------|
| `haggling_engine.py` | 750 | Dynamic pricing & negotiation | `PriceShiftEngine`, `HagglingTwin`, `generate_counter_offer()` |
| `forecasting.py` | 342 | Demand prediction | `DemandForecaster`, `predict_demand()`, `get_top_products()` |
| `graph_analytics.py` | 310 | Bundle recommendations | `ProductGraphAnalytics`, `recommend_bundle()`, `calculate_centrality()` |
| `sentiment.py` | 135 | Text sentiment scoring | `analyze_sentiment()`, `batch_analyze()` |
| `agent_workflow.py` | 200 | AI orchestration | `InventoryCopilot`, `AnalystAgent`, `AdvisorAgent` |
| `kafka_to_db.py` | 180 | Data ingestion | `KafkaConsumer`, `sync_to_postgres()` |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Redis 7+ (for blacklist)
- 4GB RAM minimum

### Installation

```powershell
# 1. Clone and navigate
cd millionx-mvp/ai-core

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
Copy-Item .env.example .env
notepad .env
```

### Environment Configuration

```env
# Database (Required)
DATABASE_URL=postgresql://millionx:millionx123@localhost:5432/millionx

# Kafka (Optional - for real-time streaming)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# OpenAI (Optional - uses rule-based fallback if not set)
OPENAI_API_KEY=sk-your-key-here
```

### Verify Installation

```powershell
# Test database connection
python -c "from forecasting import DemandForecaster; f = DemandForecaster(); print('✅ Connected')"

# Test haggling engine
python -c "from haggling_engine import PriceShiftEngine; p = PriceShiftEngine(); print('✅ PriceShift Ready')"

# Test sentiment
python -c "from sentiment import analyze_sentiment; print(analyze_sentiment('Great product!'))"
```

---

## ⚙ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | No | `localhost:9092` | Kafka broker addresses |
| `OPENAI_API_KEY` | No | - | For LLM-powered advice (optional) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `FORECAST_DAYS` | No | `7` | Default prediction horizon |
| `SIMULATION_RUNS` | No | `1000` | Monte Carlo iterations |

### Seasonal Factors (Bangladesh Context)

```python
SEASONAL_FACTORS = {
    "eid": 1.15,              # +15% during Eid ul-Fitr/Adha
    "pohela_boishakh": 1.10,  # +10% Bengali New Year
    "winter": 1.05,           # +5% Winter season
    "monsoon": 0.95,          # -5% Rainy season
    "regular": 1.00           # Normal periods
}
```

### Customer Archetypes (Haggling Twin)

```python
CUSTOMER_PROFILES = {
    "price_sensitive": {
        "weight": 0.40,           # 40% of customers
        "max_accept_premium": 5,  # Won't pay >5% above reference
        "discount_expectation": 10,
        "rounds_patience": 3
    },
    "quality_focused": {
        "weight": 0.30,
        "max_accept_premium": 15,
        "discount_expectation": 5,
        "rounds_patience": 2
    },
    "bargain_hunter": {
        "weight": 0.20,
        "max_accept_premium": 0,
        "discount_expectation": 20,
        "rounds_patience": 5
    },
    "impulse_buyer": {
        "weight": 0.10,
        "max_accept_premium": 25,
        "discount_expectation": 0,
        "rounds_patience": 1
    }
}
```

---

## 📡 API Reference

The AI Core exposes functionality through the FastAPI Risk Engine. All endpoints are prefixed with `/api/v1`.

### Forecasting

#### `GET /inventory/forecast`

Predict demand for a specific product over the next 7 days.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product identifier (e.g., `PROD-001`) |

**Response:**
```json
{
  "product_id": "PROD-001",
  "product_name": "iPhone 15 Pro Max",
  "predicted_demand": 45,
  "avg_daily_demand": 6.4,
  "restock_recommended": true,
  "confidence": 0.85,
  "forecast_period": "7 days",
  "method": "AutoARIMA"
}
```

---

### Dynamic Pricing

#### `POST /price/optimize`

Calculate optimal price using demand elasticity and market factors.

**Request Body:**
```json
{
  "product_id": "PROD-001",
  "current_price": 2500,
  "cost_price": 1800,
  "category": "Electronics"
}
```

**Response:**
```json
{
  "product_id": "PROD-001",
  "current_price": 2500,
  "optimal_price": 2079,
  "elasticity": -0.17,
  "expected_demand_change": "+8.3%",
  "season": "winter",
  "seasonal_factor": 1.05,
  "strategy": "balanced",
  "confidence": 0.82
}
```

---

#### `GET /price/competitor/{product_id}`

Get competitor price analysis for a product.

**Response:**
```json
{
  "product_id": "PROD-001",
  "our_price": 2500,
  "competitor_price": 2450,
  "price_gap_pct": 2.0,
  "recommendation": "Price is competitive",
  "season": "winter",
  "seasonal_factor": 1.05
}
```

---

### Haggling Twin

#### `POST /haggling/simulate`

Run Monte Carlo negotiation simulation (1,000 iterations).

**Request Body:**
```json
{
  "product_id": "PROD-001",
  "asking_price": 2500,
  "min_acceptable": 2000,
  "num_simulations": 1000
}
```

**Response:**
```json
{
  "conversion_rate": 0.73,
  "optimal_asking_price": 2750,
  "avg_final_price": 2340,
  "avg_discount_pct": 6.4,
  "avg_satisfaction": 0.78,
  "revenue_per_100_customers": 170820,
  "simulations_run": 1000,
  "profile_breakdown": {
    "price_sensitive": {"conversion": 0.65, "avg_discount": 12.0},
    "quality_focused": {"conversion": 0.88, "avg_discount": 3.5},
    "bargain_hunter": {"conversion": 0.45, "avg_discount": 18.0},
    "impulse_buyer": {"conversion": 0.95, "avg_discount": 1.0}
  }
}
```

---

#### `POST /haggling/counter-offer`

Generate natural language counter-offer for negotiation.

**Request Body:**
```json
{
  "product_id": "PROD-001",
  "product_name": "iPhone 15 Pro Max",
  "asking_price": 2500,
  "customer_offer": 2000,
  "min_acceptable": 1900
}
```

**Response:**
```json
{
  "original_asking": 2500,
  "customer_offer": 2000,
  "counter_offer": 2350,
  "discount_pct": 6.0,
  "accept_deal": false,
  "message": "I understand you're looking for the best value! For iPhone 15 Pro Max, I can offer 2350 BDT - that's a fair 6% discount. If you take 2 or more, I can do an extra 5% off. What do you think?",
  "strategy_used": "meet_in_middle"
}
```

---

### Sentiment Analysis

#### `POST /sentiment/analyze`

Analyze sentiment of text using VADER.

**Request Body:**
```json
{
  "texts": [
    "This product is amazing! Best purchase ever.",
    "Terrible quality, complete waste of money.",
    "It's okay, nothing special."
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "This product is amazing! Best purchase ever.",
      "label": "positive",
      "score": 0.87,
      "details": {"neg": 0.0, "neu": 0.32, "pos": 0.68, "compound": 0.87}
    },
    {
      "text": "Terrible quality, complete waste of money.",
      "label": "negative",
      "score": -0.76,
      "details": {"neg": 0.62, "neu": 0.38, "pos": 0.0, "compound": -0.76}
    },
    {
      "text": "It's okay, nothing special.",
      "label": "neutral",
      "score": 0.0,
      "details": {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    }
  ],
  "summary": {"positive": 1, "negative": 1, "neutral": 1}
}
```

---

### Graph Analytics

#### `GET /products/bundles`

Get bundle recommendations based on co-purchase patterns.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Base product for bundle |

**Response:**
```json
{
  "product_id": "PROD-001",
  "product_name": "iPhone 15 Pro Max",
  "recommended_bundles": [
    {
      "product_id": "PROD-042",
      "product_name": "AirPods Pro",
      "copurchase_frequency": 9,
      "bundle_strength": 0.85
    },
    {
      "product_id": "PROD-018",
      "product_name": "iPhone Case",
      "copurchase_frequency": 6,
      "bundle_strength": 0.72
    }
  ]
}
```

---

#### `GET /products/centrality`

Get product importance metrics using graph centrality algorithms.

**Response:**
```json
{
  "products": [
    {
      "product_id": "PROD-042",
      "product_name": "AirPods Pro",
      "pagerank": 0.3242,
      "betweenness": 0.1875,
      "degree": 5,
      "importance_score": 0.89
    },
    {
      "product_id": "PROD-001",
      "product_name": "iPhone 15 Pro Max",
      "pagerank": 0.2156,
      "betweenness": 0.1250,
      "degree": 4,
      "importance_score": 0.76
    }
  ],
  "hub_product": "PROD-042",
  "total_products_in_graph": 7
}
```

---

## 🗄 Database Schema

### PostgreSQL Tables

#### `sales_history`

Stores order data for demand forecasting and elasticity calculation.

```sql
CREATE TABLE sales_history (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255),
    product_category VARCHAR(100),
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    customer_phone VARCHAR(20),
    delivery_district VARCHAR(100),
    order_date TIMESTAMP DEFAULT NOW(),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sales_product ON sales_history(product_id);
CREATE INDEX idx_sales_date ON sales_history(order_date);
CREATE INDEX idx_sales_category ON sales_history(product_category);
```

#### `social_signals`

Stores social media data for trend detection.

```sql
CREATE TABLE social_signals (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(100) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    content TEXT,
    engagement_count INTEGER DEFAULT 0,
    sentiment_score DECIMAL(4,3),
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_social_platform ON social_signals(platform);
CREATE INDEX idx_social_date ON social_signals(posted_at);
```

### Redis Keys

| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `blacklist:{phone}` | String | 365d | Fraud blacklist |
| `price_cache:{product}` | Hash | 1h | Competitor price cache |
| `session:{id}` | Hash | 24h | User session data |

---

## 🔌 Integration Guide

### FastAPI Integration

```python
# In fastapi-risk-engine/main.py

import sys
sys.path.append("../ai-core")

from forecasting import DemandForecaster
from haggling_engine import PriceShiftEngine, HagglingTwin
from graph_analytics import ProductGraphAnalytics
from sentiment import analyze_sentiment

# Initialize engines
forecaster = DemandForecaster()
price_engine = PriceShiftEngine()
haggling_twin = HagglingTwin()
graph = ProductGraphAnalytics()

@app.get("/api/v1/inventory/forecast")
async def get_forecast(product_id: str):
    return forecaster.predict_demand(product_id)

@app.post("/api/v1/price/optimize")
async def optimize_price(request: PriceRequest):
    return price_engine.calculate_optimal_price(
        product_id=request.product_id,
        current_price=request.current_price,
        cost_price=request.cost_price
    )

@app.post("/api/v1/haggling/simulate")
async def simulate_negotiation(request: HagglingRequest):
    return haggling_twin.run_simulation(
        asking_price=request.asking_price,
        min_acceptable=request.min_acceptable
    )
```

### WhatsApp Bot Integration

```javascript
// In whatsapp-bot/index.js

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://fastapi:8000';

async function getForecast(productId) {
    const response = await axios.get(
        `${FASTAPI_URL}/api/v1/inventory/forecast?product_id=${productId}`
    );
    return response.data;
}

async function getCounterOffer(productName, askingPrice, customerOffer) {
    const response = await axios.post(
        `${FASTAPI_URL}/api/v1/haggling/counter-offer`,
        {
            product_name: productName,
            asking_price: askingPrice,
            customer_offer: customerOffer,
            min_acceptable: askingPrice * 0.8
        }
    );
    return response.data.message;
}
```

---

## 🧪 Testing

### Run Unit Tests

```powershell
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Test specific module
pytest tests/test_haggling_engine.py -v
```

### Manual API Testing

```powershell
# Test forecasting
curl "http://localhost:8000/api/v1/inventory/forecast?product_id=PROD-001"

# Test price optimization
curl -X POST "http://localhost:8000/api/v1/price/optimize" `
  -H "Content-Type: application/json" `
  -d '{"product_id":"PROD-001","current_price":2500,"cost_price":1800}'

# Test haggling simulation
curl -X POST "http://localhost:8000/api/v1/haggling/simulate" `
  -H "Content-Type: application/json" `
  -d '{"product_id":"PROD-001","asking_price":2500,"min_acceptable":2000}'
```

### Load Testing

```powershell
# Using Apache Bench (ab)
ab -n 1000 -c 10 "http://localhost:8000/api/v1/inventory/forecast?product_id=PROD-001"

# Expected: >100 req/sec for forecasting, >50 req/sec for simulations
```

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><strong>❌ "Insufficient data for forecasting"</strong></summary>

**Cause:** Less than 30 days of sales history in PostgreSQL.

**Solution:**
```powershell
# Generate mock data
cd ../millionx-phase2
python mock_data_generator.py
python mock_data_generator.py
python mock_data_generator.py

# Verify data count
python -c "from sqlalchemy import create_engine, text; e = create_engine('postgresql://millionx:millionx123@localhost:5432/millionx'); print(e.execute(text('SELECT COUNT(*) FROM sales_history')).scalar())"
```
</details>

<details>
<summary><strong>❌ "Database connection failed"</strong></summary>

**Cause:** PostgreSQL not running or incorrect credentials.

**Solution:**
```powershell
# Check Docker containers
docker ps | Select-String "postgres"

# Test connection
python -c "from sqlalchemy import create_engine; e = create_engine('postgresql://millionx:millionx123@localhost:5432/millionx'); c = e.connect(); print('✅ Connected'); c.close()"

# Check .env file
cat .env | Select-String "DATABASE_URL"
```
</details>

<details>
<summary><strong>❌ "Division by zero in HagglingTwin"</strong></summary>

**Cause:** Customer profile with `max_accept_premium=0` (bargain_hunter).

**Solution:** This was fixed in v3.0. Update to latest version:
```powershell
git pull origin main
```
</details>

<details>
<summary><strong>❌ "Decimal type error in numpy"</strong></summary>

**Cause:** PostgreSQL returns `Decimal` type, numpy expects `float`.

**Solution:** Ensure haggling_engine.py includes:
```python
df['unit_price'] = df['unit_price'].astype(float)
```
</details>

---

## ⚡ Performance

### Benchmarks (Local Docker, 16GB RAM)

| Endpoint | Avg Response | p95 | Throughput |
|----------|-------------|-----|------------|
| `/inventory/forecast` | 85ms | 150ms | 120 req/s |
| `/price/optimize` | 45ms | 80ms | 200 req/s |
| `/haggling/simulate` (1000 runs) | 320ms | 450ms | 50 req/s |
| `/haggling/counter-offer` | 25ms | 40ms | 400 req/s |
| `/sentiment/analyze` (batch=10) | 15ms | 25ms | 500 req/s |
| `/products/bundles` | 35ms | 60ms | 250 req/s |
| `/products/centrality` | 55ms | 90ms | 150 req/s |

### Memory Usage

| Component | Idle | Under Load |
|-----------|------|------------|
| FastAPI Worker | 150MB | 300MB |
| Haggling Twin (per simulation) | +50MB | +150MB |
| Graph Analytics (1000 products) | 80MB | 120MB |
| VADER Sentiment | 40MB | 45MB |

### Optimization Tips

1. **Reduce simulation runs** for faster response: `num_simulations=100`
2. **Cache competitor prices** in Redis (1-hour TTL)
3. **Pre-compute centrality** metrics on schedule (not real-time)
4. **Use connection pooling** for PostgreSQL

---

## 🤝 Contributing

### Development Setup

```powershell
# Fork and clone
git clone https://github.com/your-username/millionx-mvp.git
cd millionx-mvp/ai-core

# Create feature branch
git checkout -b feature/your-feature

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run linting
black .
flake8 .
mypy .

# Run tests
pytest tests/ -v
```

### Code Standards

- **Style:** Black formatter, 88 char line length
- **Types:** Type hints on all public functions
- **Docs:** Docstrings on all classes and public methods
- **Tests:** Minimum 80% coverage for new features

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code formatted with Black
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] README updated (if API changed)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 📚 References

- **statsforecast:** https://nixtla.github.io/statsforecast/
- **NetworkX:** https://networkx.org/documentation/
- **VADER Sentiment:** https://github.com/cjhutto/vaderSentiment
- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/

---

<div align="center">

**Built with ❤️ for South Asian SME Merchants**

MillionX Team • December 2025

[⬆ Back to Top](#-millionx-ai-core)

</div>
