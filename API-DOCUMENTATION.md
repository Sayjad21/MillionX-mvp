# 📚 MILLIONX API DOCUMENTATION

**Version:** 3.0.0  
**Last Updated:** December 25, 2025  
**Base URL:** `http://localhost:8000` (Development) | `https://api.millionx.app` (Production)

---

## 🔑 Authentication

**Current Status:** No authentication required (Hackathon MVP)  
**Future:** JWT Bearer tokens for production

**Headers (Optional):**

```http
Content-Type: application/json
Accept: application/json
```

---

## 📡 API Endpoints Overview

| Endpoint                        | Method | Purpose                        | Status |
| ------------------------------- | ------ | ------------------------------ | ------ |
| `/`                             | GET    | Root endpoint                  | ✅     |
| `/health`                       | GET    | Health check                   | ✅     |
| `/api/v1/risk-score`            | POST   | COD fraud risk analysis        | ✅     |
| `/api/v1/blacklist/add`         | POST   | Add fraudster to blacklist     | ✅     |
| `/api/v1/blacklist/check`       | GET    | Check blacklist status         | ✅     |
| `/api/v1/inventory/forecast`    | GET    | AI inventory forecasting       | ✅     |
| `/api/v1/sentiment/analyze`     | POST   | VADER sentiment analysis       | ✅ NEW |
| `/api/v1/products/bundles`      | GET    | Graph bundle recommendations   | ✅ NEW |
| `/api/v1/products/centrality`   | GET    | Product importance metrics     | ✅ NEW |
| `/api/v1/merchant/profit`       | GET    | Merchant profit summary        | ✅ NEW |
| `/api/v1/merchant/inventory`    | GET    | Merchant inventory status      | ✅ NEW |
| `/api/v1/price/optimize`        | POST   | PriceShift optimal pricing     | ✅ NEW |
| `/api/v1/price/competitor/{id}` | GET    | Competitor price analysis      | ✅ NEW |
| `/api/v1/haggling/simulate`     | POST   | Monte Carlo negotiation sim    | ✅ NEW |
| `/api/v1/haggling/counter-offer`| POST   | Smart counter-offer generator  | ✅ NEW |

---

## 1️⃣ Root Endpoint

### `GET /`

**Description:** Service information and status

**Request:**

```http
GET / HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`

```json
{
  "service": "COD Shield API",
  "version": "1.0.0",
  "status": "operational"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `service` | string | Service name |
| `version` | string | API version |
| `status` | string | Operational status |

---

## 2️⃣ Health Check

### `GET /health`

**Description:** Check service health and dependencies

**Request:**

```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "service": "COD Shield",
  "redis": "connected"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service health: `healthy` or `unhealthy` |
| `service` | string | Service name |
| `redis` | string | Redis connection status: `connected` or `disconnected` |

**Use Cases:**

- Load balancer health checks
- Monitoring/alerting systems
- Docker health checks

---

## 3️⃣ COD Risk Score Analysis

### `POST /api/v1/risk-score`

**Description:** Calculate fraud risk score for Cash-on-Delivery orders

**Request:**

```http
POST /api/v1/risk-score HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "order_id": "ORD-2025-001",
  "merchant_id": "MERCH-101",
  "customer_phone": "+8801712345678",
  "delivery_address": {
    "area": "Dhanmondi",
    "city": "Dhaka",
    "postal_code": "1205"
  },
  "order_details": {
    "total_amount": 1500.00,
    "currency": "BDT",
    "items_count": 3,
    "is_first_order": true
  },
  "timestamp": "2025-12-24T10:30:00Z"
}
```

**Request Body Schema:**

```typescript
{
  order_id: string; // Unique order identifier
  merchant_id: string; // Merchant/store ID
  customer_phone: string; // Customer phone (E.164 format recommended)
  delivery_address: {
    area: string; // Delivery area/neighborhood
    city: string; // City name
    postal_code: string; // Postal code
  }
  order_details: {
    total_amount: number; // Order total in BDT
    currency: string; // Currency code (default: "BDT")
    items_count: number; // Number of items
    is_first_order: boolean; // Is this customer's first order?
  }
  timestamp: string; // ISO 8601 timestamp
}
```

**Response:** `200 OK`

```json
{
  "order_id": "ORD-2025-001",
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "recommendation": "CONFIRMATION_CALL_REQUIRED",
  "factors": [
    {
      "factor": "HIGH_VALUE_FIRST_ORDER",
      "weight": 30,
      "description": "Order amount Tk 1500.0 for new customer"
    },
    {
      "factor": "MEDIUM_VALUE_FIRST_ORDER",
      "weight": 15,
      "description": "Order amount Tk 1500.0 for new customer"
    }
  ],
  "suggested_actions": [
    "Call customer to confirm order",
    "Verify delivery address",
    "Send SMS confirmation before dispatch"
  ],
  "processing_time_ms": 12
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `order_id` | string | Order identifier (echoed from request) |
| `risk_score` | number | Risk score 0-100 (higher = riskier) |
| `risk_level` | string | `LOW`, `MEDIUM`, or `HIGH` |
| `recommendation` | string | Suggested action code |
| `factors` | array | List of risk factors detected |
| `factors[].factor` | string | Factor code/identifier |
| `factors[].weight` | number | Points contributed to risk score |
| `factors[].description` | string | Human-readable explanation |
| `suggested_actions` | array | Recommended next steps |
| `processing_time_ms` | number | Processing time in milliseconds |

**Risk Level Thresholds:**
| Score Range | Risk Level | Recommendation |
|-------------|-----------|----------------|
| 0-40 | LOW | `PROCEED_WITH_COD` - Process normally |
| 41-70 | MEDIUM | `CONFIRMATION_CALL_REQUIRED` - Call customer |
| 71-100 | HIGH | `ADVANCE_PAYMENT_REQUIRED` - Request 50% advance |

**Risk Factors:**
| Factor Code | Max Weight | Description |
|-------------|-----------|-------------|
| `BLACKLISTED_PHONE` | 60 | Phone in blacklist (30 pts per failed delivery) |
| `HIGH_VALUE_FIRST_ORDER` | 30 | First order >1000 BDT |
| `MEDIUM_VALUE_FIRST_ORDER` | 15 | First order 500-1000 BDT |
| `RISKY_DELIVERY_AREA` | 20 | Unknown/remote delivery area |
| `SUSPICIOUS_ORDER_TIME` | 10 | Order placed 2-5 AM |

**Error Responses:**

**`500 Internal Server Error`**

```json
{
  "detail": "Risk calculation failed: <error message>"
}
```

**Example Usage (JavaScript):**

```javascript
const response = await fetch("http://localhost:8000/api/v1/risk-score", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    order_id: "ORD-2025-001",
    merchant_id: "MERCH-101",
    customer_phone: "+8801712345678",
    delivery_address: {
      area: "Dhanmondi",
      city: "Dhaka",
      postal_code: "1205",
    },
    order_details: {
      total_amount: 1500,
      currency: "BDT",
      items_count: 3,
      is_first_order: true,
    },
    timestamp: new Date().toISOString(),
  }),
});

const data = await response.json();
console.log(`Risk Score: ${data.risk_score}, Level: ${data.risk_level}`);
```

---

## 4️⃣ Add to Blacklist

### `POST /api/v1/blacklist/add`

**Description:** Add a phone number to the shared merchant blacklist

**Request:**

```http
POST /api/v1/blacklist/add HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "phone": "+8801712345678",
  "reason": "Failed delivery - Customer refused payment",
  "merchant_id": "MERCH-101"
}
```

**Request Body Schema:**

```typescript
{
  phone: string; // Phone number to blacklist
  reason: string; // Reason for blacklisting (default: "Failed delivery")
  merchant_id: string; // Merchant reporting the issue
}
```

**Response:** `200 OK`

```json
{
  "status": "added",
  "phone": "+8801712345678",
  "total_hits": 2,
  "reason": "Failed delivery - Customer refused payment"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"added"` on success |
| `phone` | string | Phone number that was blacklisted |
| `total_hits` | number | Total failed deliveries for this phone |
| `reason` | string | Reason provided in request |

**Notes:**

- Blacklist entries expire after **30 days**
- Each report increments the `total_hits` counter
- Higher `total_hits` increase risk score in future orders

**Error Responses:**

**`500 Internal Server Error`**

```json
{
  "detail": "Blacklist update failed: <error message>"
}
```

**Example Usage (JavaScript):**

```javascript
const response = await fetch("http://localhost:8000/api/v1/blacklist/add", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    phone: "+8801712345678",
    reason: "Customer refused payment at delivery",
    merchant_id: "MERCH-101",
  }),
});

const data = await response.json();
alert(`Blacklisted! Total reports: ${data.total_hits}`);
```

---

## 5️⃣ Check Blacklist Status

### `GET /api/v1/blacklist/check`

**Description:** Check if a phone number is blacklisted

**Request:**

```http
GET /api/v1/blacklist/check?phone=+8801712345678 HTTP/1.1
Host: localhost:8000
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone` | string | ✅ Yes | Phone number to check |

**Response:** `200 OK`

```json
{
  "phone": "+8801712345678",
  "is_blacklisted": true,
  "failed_deliveries": 2,
  "risk_level": "HIGH"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `phone` | string | Phone number checked |
| `is_blacklisted` | boolean | `true` if phone has failed deliveries |
| `failed_deliveries` | number | Number of failed delivery reports |
| `risk_level` | string | `LOW` (0 hits), `MEDIUM` (1 hit), `HIGH` (2+ hits) |

**Example Usage (JavaScript):**

```javascript
const phone = "+8801712345678";
const response = await fetch(
  `http://localhost:8000/api/v1/blacklist/check?phone=${encodeURIComponent(
    phone
  )}`
);

const data = await response.json();
if (data.is_blacklisted) {
  alert(
    `⚠️ Warning: ${data.failed_deliveries} failed deliveries for this customer!`
  );
}
```

---

## 6️⃣ AI Inventory Forecast (NEW)

### `GET /api/v1/inventory/forecast`

**Description:** Get AI-powered demand forecasting and restock recommendations

**Request (Batch Mode - Top Products):**

```http
GET /api/v1/inventory/forecast?limit=3 HTTP/1.1
Host: localhost:8000
```

**Request (Single Product):**

```http
GET /api/v1/inventory/forecast?product_id=PROD-130 HTTP/1.1
Host: localhost:8000
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `product_id` | string | No | - | Specific product ID (e.g., PROD-130) |
| `limit` | number | No | 5 | Number of products in batch mode |

**Response (Batch Mode):** `200 OK`

```json
{
  "count": 3,
  "products": [
    {
      "product_id": "PROD-130",
      "product_name": "Samsung Galaxy S24",
      "recommendation": "🚨 URGENT - Restock Samsung Galaxy S24!\n📊 Forecast: 35 units over next 7 days\n📈 Daily demand: 5 units/day\n🎯 Order: 42 units (with 20% safety buffer)\n⚠️ Current trend shows 200% above normal - Act now!",
      "forecast": {
        "success": true,
        "product_id": "PROD-130",
        "category": "Electronics",
        "forecast_period_days": 7,
        "predicted_demand": 35.0,
        "avg_daily_demand": 5.0,
        "recent_avg_demand": 7.0,
        "restock_recommended": true,
        "confidence_score": 0.75,
        "predictions": [
          { "date": "2025-12-25", "predicted_quantity": 5.0 },
          { "date": "2025-12-26", "predicted_quantity": 5.0 },
          { "date": "2025-12-27", "predicted_quantity": 5.0 },
          { "date": "2025-12-28", "predicted_quantity": 5.0 },
          { "date": "2025-12-29", "predicted_quantity": 5.0 },
          { "date": "2025-12-30", "predicted_quantity": 5.0 },
          { "date": "2025-12-31", "predicted_quantity": 5.0 }
        ],
        "model_metrics": {
          "training_days": 1,
          "r_squared": 0.95,
          "slope": 0.12
        }
      },
      "timestamp": "2025-12-24T01:20:00.123456"
    },
    {
      "product_id": "PROD-202",
      "product_name": "Dyson Vacuum",
      "recommendation": "⚠️ RECOMMENDED - Restock Dyson Vacuum...",
      "forecast": {
        /* same structure */
      },
      "timestamp": "2025-12-24T01:20:01.234567"
    },
    {
      "product_id": "PROD-354",
      "product_name": "Nintendo Switch",
      "recommendation": "✅ STABLE - Inventory sufficient...",
      "forecast": {
        /* same structure */
      },
      "timestamp": "2025-12-24T01:20:02.345678"
    }
  ],
  "timestamp": "2025-12-24T01:20:00"
}
```

**Response (Single Product):** `200 OK`

```json
{
  "product_id": "PROD-130",
  "product_name": "Samsung Galaxy S24",
  "recommendation": "🚨 URGENT - Restock Samsung Galaxy S24!\n📊 Forecast: 35 units over next 7 days\n📈 Daily demand: 5 units/day\n🎯 Order: 42 units (with 20% safety buffer)\n⚠️ Current trend shows 200% above normal - Act now!",
  "forecast": {
    "success": true,
    "product_id": "PROD-130",
    "category": "Electronics",
    "forecast_period_days": 7,
    "predicted_demand": 35.0,
    "avg_daily_demand": 5.0,
    "recent_avg_demand": 7.0,
    "restock_recommended": true,
    "confidence_score": 0.75,
    "predictions": [
      { "date": "2025-12-25", "predicted_quantity": 5.0 },
      { "date": "2025-12-26", "predicted_quantity": 5.0 },
      { "date": "2025-12-27", "predicted_quantity": 5.0 },
      { "date": "2025-12-28", "predicted_quantity": 5.0 },
      { "date": "2025-12-29", "predicted_quantity": 5.0 },
      { "date": "2025-12-30", "predicted_quantity": 5.0 },
      { "date": "2025-12-31", "predicted_quantity": 5.0 }
    ],
    "model_metrics": {
      "training_days": 1,
      "r_squared": 0.95,
      "slope": 0.12
    }
  },
  "timestamp": "2025-12-24T01:20:00.123456"
}
```

**Response Fields (Batch Mode):**
| Field | Type | Description |
|-------|------|-------------|
| `count` | number | Number of products in response |
| `products` | array | Array of product forecasts |
| `products[].product_id` | string | Product identifier |
| `products[].product_name` | string | Product name |
| `products[].recommendation` | string | Human-readable recommendation text |
| `products[].forecast` | object | Detailed forecast data |
| `products[].timestamp` | string | Processing timestamp (ISO 8601) |
| `timestamp` | string | Batch processing timestamp |

**Forecast Object Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if forecast succeeded |
| `product_id` | string | Product identifier |
| `category` | string | Product category |
| `forecast_period_days` | number | Forecast horizon (default: 7 days) |
| `predicted_demand` | number | Total predicted units over period |
| `avg_daily_demand` | number | Average units per day |
| `recent_avg_demand` | number | Recent historical average |
| `restock_recommended` | boolean | `true` if restock needed |
| `confidence_score` | number | Forecast confidence 0.0-1.0 |
| `predictions` | array | Daily predictions |
| `predictions[].date` | string | Date (YYYY-MM-DD) |
| `predictions[].predicted_quantity` | number | Predicted units for that day |
| `model_metrics` | object | Model performance metrics |
| `model_metrics.training_days` | number | Days of historical data used |
| `model_metrics.r_squared` | number | R² score (0.0-1.0, higher = better) |
| `model_metrics.slope` | number | Trend coefficient |

**Recommendation Urgency Levels:**
| Icon | Level | Condition | Action |
|------|-------|-----------|--------|
| 🚨 | URGENT | Predicted > 200% recent avg | Immediate restock |
| ⚠️ | RECOMMENDED | Predicted > 150% recent avg | Plan restock soon |
| ✅ | STABLE | Predicted ≤ 150% recent avg | No action needed |

**Error Responses:**

**`200 OK` (AI Core Not Available)**

```json
{
  "error": "AI Core not connected",
  "recommendation": "Please check ai-core module"
}
```

**`500 Internal Server Error`**

```json
{
  "detail": "Forecast failed: <error message>"
}
```

**Example Usage (JavaScript):**

```javascript
// Batch forecast (top 3 products)
const batchResponse = await fetch(
  "http://localhost:8000/api/v1/inventory/forecast?limit=3"
);
const batchData = await batchResponse.json();

batchData.products.forEach((product) => {
  console.log(
    `${product.product_name}: ${product.forecast.predicted_demand} units`
  );
  if (product.forecast.restock_recommended) {
    alert(`⚠️ Restock ${product.product_name}!`);
  }
});

// Single product forecast
const productId = "PROD-130";
const singleResponse = await fetch(
  `http://localhost:8000/api/v1/inventory/forecast?product_id=${productId}`
);
const singleData = await singleResponse.json();

console.log(`Forecast for ${singleData.product_name}:`);
console.log(`- Predicted: ${singleData.forecast.predicted_demand} units`);
console.log(
  `- Confidence: ${(singleData.forecast.confidence_score * 100).toFixed(0)}%`
);
console.log(
  `- Restock: ${singleData.forecast.restock_recommended ? "Yes" : "No"}`
);
```

**React Component Example:**

```jsx
import { useState, useEffect } from "react";

function InventoryForecast({ productId }) {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(
      `http://localhost:8000/api/v1/inventory/forecast?product_id=${productId}`
    )
      .then((res) => res.json())
      .then((data) => {
        setForecast(data);
        setLoading(false);
      });
  }, [productId]);

  if (loading) return <div>Loading forecast...</div>;

  return (
    <div className="forecast-card">
      <h3>{forecast.product_name}</h3>
      <div
        className={forecast.forecast.restock_recommended ? "urgent" : "stable"}
      >
        <p>{forecast.recommendation}</p>
        <div className="metrics">
          <span>Predicted: {forecast.forecast.predicted_demand} units</span>
          <span>
            Confidence: {(forecast.forecast.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="predictions">
        {forecast.forecast.predictions.map((day) => (
          <div key={day.date}>
            {day.date}: {day.predicted_quantity} units
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 7️⃣ Sentiment Analysis

### `POST /api/v1/sentiment/analyze`

**Description:** Analyze sentiment of text using VADER (Valence Aware Dictionary and sEntiment Reasoner)

**Request:**

```http
POST /api/v1/sentiment/analyze HTTP/1.1
Host: localhost:8000
Content-Type: application/json

["This product is amazing!", "Terrible quality, waste of money", "Its okay, nothing special"]
```

**Request Body Schema:**

```typescript
string[]  // Array of texts to analyze
```

**Response:** `200 OK`

```json
{
  "results": [
    {
      "text": "This product is amazing!",
      "label": "positive",
      "score": 0.6239,
      "details": {
        "neg": 0.0,
        "neu": 0.423,
        "pos": 0.577,
        "compound": 0.6239
      }
    },
    {
      "text": "Terrible quality, waste of money",
      "label": "negative",
      "score": -0.7096,
      "details": {
        "neg": 0.663,
        "neu": 0.337,
        "pos": 0.0,
        "compound": -0.7096
      }
    },
    {
      "text": "Its okay, nothing special",
      "label": "negative",
      "score": -0.092,
      "details": {
        "neg": 0.367,
        "neu": 0.325,
        "pos": 0.309,
        "compound": -0.092
      }
    }
  ],
  "aggregate": {
    "total_texts": 3,
    "positive": 1,
    "negative": 2,
    "neutral": 0
  },
  "model": "VADER Sentiment Analysis"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `results` | array | Individual sentiment results |
| `results[].text` | string | Original text analyzed |
| `results[].label` | string | `positive`, `negative`, or `neutral` |
| `results[].score` | number | Compound score (-1.0 to 1.0) |
| `results[].details.neg` | number | Negative proportion (0-1) |
| `results[].details.neu` | number | Neutral proportion (0-1) |
| `results[].details.pos` | number | Positive proportion (0-1) |
| `results[].details.compound` | number | Normalized compound score |
| `aggregate.total_texts` | number | Total texts analyzed |
| `aggregate.positive` | number | Count of positive texts |
| `aggregate.negative` | number | Count of negative texts |
| `aggregate.neutral` | number | Count of neutral texts |
| `model` | string | Model used for analysis |

**Label Thresholds:**
| Compound Score | Label |
|----------------|-------|
| >= 0.05 | positive |
| <= -0.05 | negative |
| -0.05 < score < 0.05 | neutral |

---

## 8️⃣ Product Bundle Recommendations

### `GET /api/v1/products/bundles`

**Description:** Get product bundle recommendations based on co-purchase patterns using graph analytics

**Request:**

```http
GET /api/v1/products/bundles?product_id=PROD-001&limit=3 HTTP/1.1
Host: localhost:8000
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `product_id` | string | ✅ Yes | - | Product ID to find bundles for |
| `limit` | number | No | 3 | Maximum recommendations to return |

**Response:** `200 OK`

```json
{
  "product_id": "PROD-001",
  "recommendations": [
    {
      "product_id": "PROD-042",
      "product_name": "AirPods Pro",
      "category": "accessories",
      "copurchase_frequency": 9,
      "recommendation_score": 1.0,
      "avg_price": 65025.27
    }
  ],
  "model": "NetworkX Graph Analytics"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `product_id` | string | Input product ID |
| `recommendations` | array | Recommended bundle products |
| `recommendations[].product_id` | string | Recommended product ID |
| `recommendations[].product_name` | string | Recommended product name |
| `recommendations[].category` | string | Product category |
| `recommendations[].copurchase_frequency` | number | Times bought together |
| `recommendations[].recommendation_score` | number | Score 0-1 (higher = stronger) |
| `recommendations[].avg_price` | number | Average price in BDT |
| `model` | string | Analytics model used |

---

## 9️⃣ Product Centrality Metrics

### `GET /api/v1/products/centrality`

**Description:** Get product importance metrics using graph centrality algorithms

**Request:**

```http
GET /api/v1/products/centrality HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`

```json
{
  "centrality_metrics": {
    "PROD-001": {
      "pagerank": 0.1664,
      "betweenness": 0.0,
      "degree": 9,
      "importance_score": 0.2469
    },
    "PROD-042": {
      "pagerank": 0.2085,
      "betweenness": 0.0667,
      "degree": 11,
      "importance_score": 0.3242
    },
    "PROD-002": {
      "pagerank": 0.1429,
      "betweenness": 0.0,
      "degree": 4,
      "importance_score": 0.1442
    }
  },
  "model": "NetworkX Graph Analytics",
  "metrics": ["PageRank", "Betweenness Centrality", "Degree Centrality"]
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `centrality_metrics` | object | Map of product_id to metrics |
| `centrality_metrics[id].pagerank` | number | PageRank importance (0-1) |
| `centrality_metrics[id].betweenness` | number | Bridge connectivity (0-1) |
| `centrality_metrics[id].degree` | number | Number of connections |
| `centrality_metrics[id].importance_score` | number | Combined score (0-1) |
| `model` | string | Analytics model used |
| `metrics` | array | List of metrics calculated |

**Metrics Explained:**
| Metric | Description |
|--------|-------------|
| PageRank | How often this product appears in purchase chains |
| Betweenness | How often this product bridges different product clusters |
| Degree | Number of products frequently bought with this one |
| Importance Score | Weighted combination of all metrics |

---

## 🔟 Merchant Profit Summary

### `GET /api/v1/merchant/profit`

**Description:** Get merchant profit summary with trends and top sellers

**Request:**

```http
GET /api/v1/merchant/profit?merchant_id=demo&period=month HTTP/1.1
Host: localhost:8000
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `merchant_id` | string | No | `demo` | Merchant identifier |
| `period` | string | No | `month` | `week`, `month`, or `year` |

**Response:** `200 OK`

```json
{
  "period": "This Month",
  "merchant_id": "demo",
  "revenue": 2244564.76,
  "estimated_costs": 1571195.33,
  "net_profit": 673369.43,
  "profit_margin_pct": 30.0,
  "total_orders": 21,
  "total_units_sold": 112,
  "avg_order_value": 106884.04,
  "top_seller": {
    "product": "Adidas Ultraboost",
    "units_sold": 13
  },
  "trend_vs_previous": "-97%",
  "currency": "BDT",
  "generated_at": "2025-12-24T19:38:06.654128"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `period` | string | Time period analyzed |
| `merchant_id` | string | Merchant identifier |
| `revenue` | number | Total revenue in BDT |
| `estimated_costs` | number | Estimated costs (70% of revenue) |
| `net_profit` | number | Revenue minus costs |
| `profit_margin_pct` | number | Profit as percentage of revenue |
| `total_orders` | number | Number of orders in period |
| `total_units_sold` | number | Total units sold |
| `avg_order_value` | number | Average order value in BDT |
| `top_seller.product` | string | Best selling product name |
| `top_seller.units_sold` | number | Units sold of top product |
| `trend_vs_previous` | string | Comparison to previous period |
| `currency` | string | Currency code |
| `generated_at` | string | Timestamp (ISO 8601) |

---

## 1️⃣1️⃣ Merchant Inventory Status

### `GET /api/v1/merchant/inventory`

**Description:** Get merchant inventory status with low stock alerts and trends

**Request:**

```http
GET /api/v1/merchant/inventory?merchant_id=demo&threshold=10 HTTP/1.1
Host: localhost:8000
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `merchant_id` | string | No | `demo` | Merchant identifier |
| `threshold` | number | No | `10` | Low stock alert threshold |

**Response:** `200 OK`

```json
{
  "merchant_id": "demo",
  "total_products": 69,
  "low_stock_count": 0,
  "low_stock_alerts": [],
  "trending_products": [
    "Lenovo ThinkPad",
    "Adidas Ultraboost",
    "Philips Air Fryer"
  ],
  "inventory_summary": [
    {
      "product_id": "PROD-014",
      "product_name": "Lenovo ThinkPad",
      "category": "laptop",
      "estimated_stock": 17,
      "monthly_velocity": 108,
      "days_until_stockout": 4,
      "status": "NORMAL"
    }
  ],
  "tip": "All stock levels healthy!",
  "generated_at": "2025-12-24T19:38:12.945084"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `merchant_id` | string | Merchant identifier |
| `total_products` | number | Total tracked products |
| `low_stock_count` | number | Products below threshold |
| `low_stock_alerts` | array | Products needing restock |
| `trending_products` | array | Top 3 fast-moving products |
| `inventory_summary` | array | Top 10 products by velocity |
| `inventory_summary[].product_id` | string | Product identifier |
| `inventory_summary[].product_name` | string | Product name |
| `inventory_summary[].category` | string | Product category |
| `inventory_summary[].estimated_stock` | number | Estimated units in stock |
| `inventory_summary[].monthly_velocity` | number | Units sold per month |
| `inventory_summary[].days_until_stockout` | number | Days until out of stock |
| `inventory_summary[].status` | string | `LOW` or `NORMAL` |
| `tip` | string | Actionable recommendation |
| `generated_at` | string | Timestamp (ISO 8601) |

---

## 1️⃣2️⃣ PriceShift - Price Optimization

### `POST /api/v1/price/optimize`

**Description:** Get optimal price recommendation using demand elasticity and market factors

**Request:**

```http
POST /api/v1/price/optimize HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "product_id": "PROD-001",
  "current_price": 2500,
  "cost": 1800,
  "category": "Electronics",
  "strategy": "balanced"
}
```

**Request Body Schema:**

```typescript
{
  product_id: string;      // Product identifier
  current_price: number;   // Current selling price in BDT
  cost: number;            // Product cost in BDT
  category?: string;       // Product category (optional)
  strategy?: string;       // "aggressive", "balanced", or "conservative"
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "product_id": "PROD-001",
  "current_price": 2500.0,
  "optimal_price": 2079.0,
  "price_change_pct": -16.8,
  "expected_margin_pct": 13.4,
  "elasticity": -0.17,
  "competitor_price": 142179.8,
  "season": "winter",
  "seasonal_factor": 1.05,
  "strategy": "balanced",
  "confidence": 0.7,
  "recommendation": "Decrease price by Tk 421 (17%) to boost conversions. Competitor pricing at Tk 142180.",
  "model": "PriceShift Elasticity Engine"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether optimization succeeded |
| `product_id` | string | Product identifier |
| `current_price` | number | Current price in BDT |
| `optimal_price` | number | Recommended price in BDT |
| `price_change_pct` | number | Percentage change recommended |
| `expected_margin_pct` | number | Expected profit margin |
| `elasticity` | number | Price elasticity coefficient |
| `competitor_price` | number | Simulated competitor price |
| `season` | string | Current season detected |
| `seasonal_factor` | number | Seasonal price multiplier |
| `strategy` | string | Pricing strategy used |
| `confidence` | number | Confidence score (0-1) |
| `recommendation` | string | Natural language advice |
| `model` | string | Model used |

**Pricing Strategies:**
| Strategy | Description |
|----------|-------------|
| `aggressive` | Maximize profit, higher prices |
| `balanced` | Balance profit and conversion |
| `conservative` | Prioritize sales volume, lower prices |

**Seasonal Factors (Bangladesh):**
| Season | Factor | Description |
|--------|--------|-------------|
| `eid` | 1.15 | Eid ul-Fitr/Adha premium |
| `pohela_boishakh` | 1.10 | Bengali New Year |
| `winter` | 1.05 | Winter season |
| `monsoon` | 0.95 | Rainy season discount |
| `regular` | 1.0 | Normal periods |

---

## 1️⃣3️⃣ Competitor Price Analysis

### `GET /api/v1/price/competitor/{product_id}`

**Description:** Get competitor price analysis for a product

**Request:**

```http
GET /api/v1/price/competitor/PROD-001 HTTP/1.1
Host: localhost:8000
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | ✅ Yes | Product ID to analyze |

**Response:** `200 OK`

```json
{
  "product_id": "PROD-001",
  "competitor_price": 146905.38,
  "current_season": "winter",
  "seasonal_factor": 1.05,
  "note": "Competitor prices are simulated. In production, integrates with Daraz/AliExpress APIs."
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `product_id` | string | Product identifier |
| `competitor_price` | number | Simulated competitor price in BDT |
| `current_season` | string | Current season |
| `seasonal_factor` | number | Seasonal multiplier |
| `note` | string | Implementation note |

---

## 1️⃣4️⃣ Haggling Twin - Negotiation Simulation

### `POST /api/v1/haggling/simulate`

**Description:** Run Monte Carlo simulation for negotiation outcomes. Simulates 1,000 customer negotiations to predict optimal pricing strategy.

**Request:**

```http
POST /api/v1/haggling/simulate HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "product_id": "PROD-001",
  "asking_price": 2500,
  "cost": 1800,
  "num_simulations": 1000
}
```

**Request Body Schema:**

```typescript
{
  product_id: string;       // Product identifier
  asking_price: number;     // Starting price in BDT
  cost: number;             // Product cost in BDT
  num_simulations?: number; // Simulations to run (default: 1000)
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "product_id": "PROD-001",
  "asking_price": 2500.0,
  "simulations_run": 1000,
  "results": {
    "conversion_rate": 1.0,
    "avg_final_price": 2500.0,
    "avg_discount_pct": 0.0,
    "avg_negotiation_rounds": 1.0,
    "customer_satisfaction": 1.0,
    "deals_closed": 1000,
    "deals_lost": 0
  },
  "expected_revenue_per_100_customers": 250000.0,
  "optimal_asking_price": 2750.0,
  "optimal_expected_revenue": 275000.0,
  "by_customer_profile": {
    "bargain_hunter": {
      "deal_closed": 1.0,
      "final_price": 2500.0,
      "discount_pct": 0.0
    },
    "impulse_buyer": {
      "deal_closed": 1.0,
      "final_price": 2500.0,
      "discount_pct": 0.0
    },
    "price_sensitive": {
      "deal_closed": 1.0,
      "final_price": 2500.0,
      "discount_pct": 0.0
    },
    "quality_focused": {
      "deal_closed": 1.0,
      "final_price": 2500.0,
      "discount_pct": 0.0
    }
  },
  "recommendation": "✅ Strong conversion (100%). You can start higher at Tk 2750. Most customers accept with minimal negotiation.",
  "model": "Haggling Twin Monte Carlo Simulator"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether simulation succeeded |
| `product_id` | string | Product identifier |
| `asking_price` | number | Input asking price |
| `simulations_run` | number | Number of simulations run |
| `results.conversion_rate` | number | Percentage of deals closed (0-1) |
| `results.avg_final_price` | number | Average closing price |
| `results.avg_discount_pct` | number | Average discount given |
| `results.avg_negotiation_rounds` | number | Average rounds to close |
| `results.customer_satisfaction` | number | Average satisfaction (0-1) |
| `results.deals_closed` | number | Number of successful deals |
| `results.deals_lost` | number | Number of lost deals |
| `expected_revenue_per_100_customers` | number | Projected revenue |
| `optimal_asking_price` | number | Recommended starting price |
| `optimal_expected_revenue` | number | Revenue at optimal price |
| `by_customer_profile` | object | Results by customer type |
| `recommendation` | string | Natural language strategy |
| `model` | string | Model used |

**Customer Profiles:**
| Profile | Weight | Description |
|---------|--------|-------------|
| `price_sensitive` | 40% | Will accept up to 5% premium, walks away at 15% |
| `quality_focused` | 30% | Accepts 20% premium, walks away at 35% |
| `bargain_hunter` | 20% | Accepts no premium, walks away at 10% |
| `impulse_buyer` | 10% | Accepts 30% premium, rarely walks away |

---

## 1️⃣5️⃣ Haggling Engine - Counter-Offer Generator

### `POST /api/v1/haggling/counter-offer`

**Description:** Generate smart counter-offer for real-time negotiation. Powers natural language responses like "Can't do 500, but 520 for two? Deal?"

**Request:**

```http
POST /api/v1/haggling/counter-offer HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "asking_price": 2500,
  "customer_offer": 2000,
  "cost": 1800,
  "round_number": 1
}
```

**Request Body Schema:**

```typescript
{
  asking_price: number;    // Your original asking price in BDT
  customer_offer: number;  // Customer's offer in BDT
  cost: number;            // Product cost in BDT
  round_number?: number;   // Negotiation round (default: 1)
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "customer_offer": 2000.0,
  "counter_offer": 2350.0,
  "discount_from_asking": 6.0,
  "margin_pct": 23.4,
  "accept_deal": false,
  "message": "Tk 2000 is too low bhai. How about Tk 2350? Premium quality! ⭐ Or get 2 for Tk 4465 - better value!",
  "negotiation_round": 1,
  "next_move": "await_response",
  "model": "Haggling Engine Counter-Offer Generator"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether generation succeeded |
| `customer_offer` | number | Customer's offer (echoed) |
| `counter_offer` | number | Generated counter-offer in BDT |
| `discount_from_asking` | number | Discount percentage from asking |
| `margin_pct` | number | Profit margin at counter-offer |
| `accept_deal` | boolean | Whether to accept customer's offer |
| `message` | string | Natural language response |
| `negotiation_round` | number | Current round number |
| `next_move` | string | `close_deal` or `await_response` |
| `model` | string | Model used |

**Counter-Offer Logic:**
| Gap from Asking | Response Strategy |
|-----------------|-------------------|
| ≤ 5% | Accept deal |
| 5-15% | Meet in the middle |
| 15-30% | Counter at 70% of gap |
| > 30% | Counter at 10% discount max |

**Quantity Incentives:**
When gap > 10%, adds quantity discount suggestion (5% off for 2+ items).

---

## 🔧 Error Handling

### Standard Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Status                | Description                               |
| ---- | --------------------- | ----------------------------------------- |
| 200  | OK                    | Request succeeded                         |
| 400  | Bad Request           | Invalid request parameters                |
| 404  | Not Found             | Endpoint not found                        |
| 422  | Unprocessable Entity  | Validation error (missing/invalid fields) |
| 500  | Internal Server Error | Server-side error                         |

### Validation Errors (422)

When request validation fails, FastAPI returns detailed error info:

```json
{
  "detail": [
    {
      "loc": ["body", "delivery_address", "postal_code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Fields:**

- `loc`: Location of error (e.g., `["body", "field_name"]`)
- `msg`: Error message
- `type`: Error type code

---

## 🚀 Rate Limiting

**Current Status:** No rate limiting (Hackathon MVP)

**Future Implementation:**

- 100 requests/minute per IP
- 1000 requests/hour per merchant_id
- Burst allowance: 20 requests/second

---

## 📊 Response Times (SLA)

| Endpoint                     | Target | Actual | Status |
| ---------------------------- | ------ | ------ | ------ |
| `/health`                    | <10ms  | ~5ms   | ✅     |
| `/api/v1/risk-score`         | <50ms  | ~30ms  | ✅     |
| `/api/v1/blacklist/*`        | <20ms  | ~10ms  | ✅     |
| `/api/v1/inventory/forecast` | <100ms | ~50ms  | ✅     |

---

## 🔗 CORS Configuration

**Allowed Origins (Development):**

```
http://localhost:3000
http://localhost:3001
http://localhost:5173
```

**Allowed Methods:**

```
GET, POST, PUT, DELETE, OPTIONS
```

**Allowed Headers:**

```
Content-Type, Authorization, Accept
```

---

## 🧪 Testing with cURL

### Health Check

```bash
curl http://localhost:8000/health
```

### Risk Score

```bash
curl -X POST http://localhost:8000/api/v1/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-TEST-001",
    "merchant_id": "MERCH-101",
    "customer_phone": "+8801712345678",
    "delivery_address": {
      "area": "Dhanmondi",
      "city": "Dhaka",
      "postal_code": "1205"
    },
    "order_details": {
      "total_amount": 1500,
      "currency": "BDT",
      "items_count": 3,
      "is_first_order": true
    },
    "timestamp": "2025-12-24T10:30:00Z"
  }'
```

### Blacklist Add

```bash
curl -X POST http://localhost:8000/api/v1/blacklist/add \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+8801712345678",
    "reason": "Test blacklist entry",
    "merchant_id": "MERCH-101"
  }'
```

### Blacklist Check

```bash
curl "http://localhost:8000/api/v1/blacklist/check?phone=%2B8801712345678"
```

### Inventory Forecast (Batch)

```bash
curl "http://localhost:8000/api/v1/inventory/forecast?limit=3"
```

### Inventory Forecast (Single)

```bash
curl "http://localhost:8000/api/v1/inventory/forecast?product_id=PROD-130"
```

---

## 📱 Frontend Integration Examples

### React + TypeScript

```typescript
// types/api.ts
export interface RiskScoreRequest {
  order_id: string;
  merchant_id: string;
  customer_phone: string;
  delivery_address: {
    area: string;
    city: string;
    postal_code: string;
  };
  order_details: {
    total_amount: number;
    currency: string;
    items_count: number;
    is_first_order: boolean;
  };
  timestamp: string;
}

export interface RiskScoreResponse {
  order_id: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  recommendation: string;
  factors: Array<{
    factor: string;
    weight: number;
    description: string;
  }>;
  suggested_actions: string[];
  processing_time_ms: number;
}

export interface ForecastResponse {
  product_id: string;
  product_name: string;
  recommendation: string;
  forecast: {
    success: boolean;
    predicted_demand: number;
    avg_daily_demand: number;
    restock_recommended: boolean;
    confidence_score: number;
    predictions: Array<{
      date: string;
      predicted_quantity: number;
    }>;
  };
  timestamp: string;
}

// services/api.ts
const API_BASE_URL = "http://localhost:8000";

export const apiClient = {
  async getRiskScore(order: RiskScoreRequest): Promise<RiskScoreResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/risk-score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(order),
    });

    if (!response.ok) {
      throw new Error(`Risk score failed: ${response.statusText}`);
    }

    return response.json();
  },

  async getForecast(
    productId?: string,
    limit?: number
  ): Promise<ForecastResponse> {
    const params = new URLSearchParams();
    if (productId) params.set("product_id", productId);
    if (limit) params.set("limit", limit.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/inventory/forecast?${params}`
    );

    if (!response.ok) {
      throw new Error(`Forecast failed: ${response.statusText}`);
    }

    return response.json();
  },

  async checkBlacklist(phone: string) {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/blacklist/check?phone=${encodeURIComponent(
        phone
      )}`
    );
    return response.json();
  },

  async addToBlacklist(phone: string, reason: string, merchantId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/blacklist/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, reason, merchant_id: merchantId }),
    });
    return response.json();
  },
};
```

### Vue 3 + Composition API

```typescript
// composables/useApi.ts
import { ref } from "vue";

export function useRiskScore() {
  const loading = ref(false);
  const error = ref<Error | null>(null);
  const data = ref(null);

  const checkRisk = async (order: any) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch("http://localhost:8000/api/v1/risk-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(order),
      });

      if (!response.ok) throw new Error("Risk check failed");
      data.value = await response.json();
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  };

  return { loading, error, data, checkRisk };
}
```

### Next.js API Routes

```typescript
// app/api/forecast/route.ts
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const productId = searchParams.get("product_id");
  const limit = searchParams.get("limit") || "5";

  const params = new URLSearchParams();
  if (productId) params.set("product_id", productId);
  else params.set("limit", limit);

  const response = await fetch(
    `http://fastapi:8000/api/v1/inventory/forecast?${params}`
  );

  const data = await response.json();
  return NextResponse.json(data);
}
```

---

## 🔐 Security Best Practices

### For Frontend Developers

1. **Never expose API keys in frontend code**
2. **Validate user input before sending to API**
3. **Use HTTPS in production**
4. **Implement request timeout (5-10 seconds)**
5. **Handle errors gracefully with user-friendly messages**
6. **Sanitize phone numbers (remove spaces, dashes)**
7. **Format timestamps in ISO 8601**

### Input Validation Example

```typescript
function validatePhone(phone: string): string {
  // Remove spaces, dashes, parentheses
  const cleaned = phone.replace(/[\s\-\(\)]/g, "");

  // Ensure starts with +880 or convert
  if (cleaned.startsWith("0")) {
    return "+880" + cleaned.substring(1);
  }
  if (!cleaned.startsWith("+")) {
    return "+" + cleaned;
  }
  return cleaned;
}

function validateOrderAmount(amount: number): boolean {
  return amount > 0 && amount < 1000000; // Max 1M BDT
}
```

---

## 📞 Support & Feedback

**Issues:** Report bugs via GitHub Issues  
**Questions:** Join our Discord server  
**Email:** dev@millionx.app

**API Changelog:** See [CHANGELOG.md](CHANGELOG.md)

---

## 🎯 Quick Reference

| Need                          | Endpoint                        | Method |
| ----------------------------- | ------------------------------- | ------ |
| Check if API is up            | `/health`                       | GET    |
| Calculate fraud risk          | `/api/v1/risk-score`            | POST   |
| Report fraudster              | `/api/v1/blacklist/add`         | POST   |
| Check if customer is risky    | `/api/v1/blacklist/check`       | GET    |
| Get AI inventory forecast     | `/api/v1/inventory/forecast`    | GET    |
| Analyze text sentiment        | `/api/v1/sentiment/analyze`     | POST   |
| Get bundle recommendations    | `/api/v1/products/bundles`      | GET    |
| Get product importance        | `/api/v1/products/centrality`   | GET    |
| Get profit summary            | `/api/v1/merchant/profit`       | GET    |
| Check inventory status        | `/api/v1/merchant/inventory`    | GET    |
| Get optimal price             | `/api/v1/price/optimize`        | POST   |
| Check competitor prices       | `/api/v1/price/competitor/{id}` | GET    |
| Simulate negotiations         | `/api/v1/haggling/simulate`     | POST   |
| Generate counter-offer        | `/api/v1/haggling/counter-offer`| POST   |

**Base URL:** `http://localhost:8000`  
**API Docs (Swagger):** `http://localhost:8000/docs`  
**API Docs (ReDoc):** `http://localhost:8000/redoc`

---

**Generated:** December 25, 2025  
**Maintained by:** MillionX Development Team
