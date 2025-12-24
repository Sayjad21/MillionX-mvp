# 📚 MILLIONX API DOCUMENTATION

**Version:** 2.0.0  
**Last Updated:** December 24, 2025  
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

| Endpoint                     | Method | Purpose                    | Status |
| ---------------------------- | ------ | -------------------------- | ------ |
| `/`                          | GET    | Root endpoint              | ✅     |
| `/health`                    | GET    | Health check               | ✅     |
| `/api/v1/risk-score`         | POST   | COD fraud risk analysis    | ✅     |
| `/api/v1/blacklist/add`      | POST   | Add fraudster to blacklist | ✅     |
| `/api/v1/blacklist/check`    | GET    | Check blacklist status     | ✅     |
| `/api/v1/inventory/forecast` | GET    | AI inventory forecasting   | ✅ NEW |

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

| Need                       | Endpoint                     | Method |
| -------------------------- | ---------------------------- | ------ |
| Check if API is up         | `/health`                    | GET    |
| Calculate fraud risk       | `/api/v1/risk-score`         | POST   |
| Report fraudster           | `/api/v1/blacklist/add`      | POST   |
| Check if customer is risky | `/api/v1/blacklist/check`    | GET    |
| Get AI inventory forecast  | `/api/v1/inventory/forecast` | GET    |

**Base URL:** `http://localhost:8000`  
**API Docs (Swagger):** `http://localhost:8000/docs`  
**API Docs (ReDoc):** `http://localhost:8000/redoc`

---

**Generated:** December 24, 2025  
**Maintained by:** MillionX Development Team
