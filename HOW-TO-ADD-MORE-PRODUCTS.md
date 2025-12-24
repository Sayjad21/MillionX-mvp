# Adding More Products to MillionX Frontend

## Current Setup: How Product Data Flows

### 1. **Data Source: SQLite Database**

- **Location:** `ai-core/millionx_ai.db`
- **Table:** `sales_history`
- **Contains:** 50 sales records with 30 unique products across categories:
  - 📱 Smartphones: iPhone 15, Samsung Galaxy S24, Xiaomi, OnePlus, Vivo
  - 💻 Laptops: MacBook Pro, Dell XPS 15, Lenovo ThinkPad, Asus ROG, MSI
  - 📺 Electronics: Samsung TV, Sony headphones, AirPods, Canon cameras
  - 👟 Fashion: Nike, Adidas, Gucci
  - 🏠 Home Appliances: Dyson, Philips, Samsung Refrigerator, Instant Pot

### 2. **Data Generation Script**

- **File:** `millionx-phase2/mock_data_generator.py`
- **What it does:** Generates fake sales history and saves to SQLite
- **Product categories:**
  ```python
  PRODUCT_CATEGORIES = {
      'smartphone': ['iPhone 15 Pro Max', 'Samsung Galaxy S24', ...],
      'laptop': ['MacBook Pro M3', 'Dell XPS 15', ...],
      'fashion': ['Nike Air Max', 'Adidas Ultraboost', ...],
      'electronics': ['Sony WH-1000XM5', 'AirPods Pro', ...],
      'home': ['Philips Air Fryer', 'Dyson Vacuum', ...]
  }
  ```

### 3. **AI Forecasting Pipeline**

- **File:** `ai-core/forecasting.py` → `get_top_products(limit=10)`
- **What it does:** Queries database for top-selling products based on:
  - Total quantity sold in last 30 days
  - Number of orders
  - Returns top N products (default: 5)

### 4. **FastAPI Backend**

- **Endpoint:** `GET /api/v1/inventory/forecast?limit=5`
- **Process:**
  1. Calls `copilot.process_batch(limit=5)`
  2. Gets top 5 products from SQLite
  3. Runs AI forecast for each (Linear Regression)
  4. Returns JSON with predictions + recommendations

### 5. **Frontend Display**

- **Component:** `CommandCenter.jsx`
- **API Call:** `getInventoryForecast(limit=10)`
- **Currently shows:** Only top 5-10 products with AI forecasts

---

## 🎯 How to Add More Products (3 Options)

### **Option 1: Increase Limit (Easiest - 2 minutes)**

This shows more of the existing 30 products by increasing the limit parameter.

#### Frontend Change:

**File:** `frontend/src/components/CommandCenter.jsx`

```javascript
// Line ~30
const fetchForecasts = async () => {
  setLoading(true);
  setError(null);

  try {
    // Change from 10 to 30 to show all available products
    const data = await getInventoryForecast(30); // ← Change this number
```

**Result:** Shows all 30 existing products from database

---

### **Option 2: Add More Mock Data (Medium - 10 minutes)**

Add more products to the database by running the generator script with modified categories.

#### Step 1: Edit Product Categories

**File:** `millionx-phase2/mock_data_generator.py`

```python
# Around line 40, ADD MORE PRODUCTS:
PRODUCT_CATEGORIES = {
    'smartphone': [
        'iPhone 15 Pro Max', 'Samsung Galaxy S24', 'Xiaomi Redmi Note 13',
        'OnePlus 12', 'Google Pixel 8', 'Vivo V30', 'Oppo Reno 11',
        'Realme 11 Pro', 'Nothing Phone 2', 'Honor Magic 6'  # ← NEW
    ],
    'laptop': [
        'MacBook Pro M3', 'Dell XPS 15', 'HP Pavilion', 'Lenovo ThinkPad',
        'Asus ROG', 'Acer Aspire', 'MSI Gaming Laptop',
        'Surface Laptop 5', 'Razer Blade 15', 'LG Gram'  # ← NEW
    ],
    'wearables': [  # ← NEW CATEGORY
        'Apple Watch Series 9', 'Samsung Galaxy Watch 6', 'Fitbit Charge 6',
        'Garmin Forerunner', 'Amazfit GTR 4', 'Xiaomi Mi Band 8'
    ],
    'tablets': [  # ← NEW CATEGORY
        'iPad Pro M2', 'Samsung Galaxy Tab S9', 'Microsoft Surface Pro 9',
        'Lenovo Tab P12', 'Xiaomi Pad 6', 'Amazon Fire HD'
    ],
    'gaming': [  # ← NEW CATEGORY
        'PS5 Console', 'Xbox Series X', 'Nintendo Switch OLED',
        'Steam Deck', 'Meta Quest 3', 'Asus ROG Ally'
    ],
    # Keep existing: fashion, electronics, home
}
```

#### Step 2: Clear Old Data & Regenerate

```bash
# Delete old database
rm ai-core/millionx_ai.db

# Run generator (it will create new db with your products)
cd ai-core
python agent_workflow.py
```

#### Step 3: Restart Backend

```bash
cd ..
docker-compose up -d --build fastapi
```

**Result:** Database now has 60-100 products across 8 categories

---

### **Option 3: Combine Real + AI-Generated Products (Advanced - 30 minutes)**

Create a hybrid endpoint that shows:

- AI forecasts for top sellers (existing)
- Static product catalog for all inventory (new)

#### Step 1: Create Product Catalog JSON

**File:** `ai-core/product_catalog.json`

```json
{
  "products": [
    {
      "product_id": "PROD-WATCH-001",
      "product_name": "Apple Watch Series 9",
      "category": "wearables",
      "base_price": 45000,
      "stock_status": "In Stock",
      "image_url": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d"
    },
    {
      "product_id": "PROD-GAME-001",
      "product_name": "PlayStation 5",
      "category": "gaming",
      "base_price": 65000,
      "stock_status": "Low Stock",
      "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3"
    }
    // ... add 50+ more products
  ]
}
```

#### Step 2: Add Catalog Endpoint

**File:** `fastapi-risk-engine/main.py`

```python
import json

@app.get("/api/v1/inventory/catalog")
async def get_product_catalog(category: str = None):
    """Get full product catalog (no AI forecast)"""
    with open('/ai-core/product_catalog.json') as f:
        catalog = json.load(f)

    products = catalog['products']

    # Filter by category if specified
    if category:
        products = [p for p in products if p['category'] == category]

    return {
        "count": len(products),
        "products": products
    }
```

#### Step 3: Update Frontend to Merge Data

**File:** `frontend/src/api.js`

```javascript
export const getProductCatalog = async (category = null) => {
  const response = await api.get("/api/v1/inventory/catalog", {
    params: { category },
  });
  return response.data;
};
```

**File:** `frontend/src/components/CommandCenter.jsx`

```javascript
const fetchForecasts = async () => {
  setLoading(true);
  try {
    // Get AI forecasts for top sellers
    const forecastData = await getInventoryForecast(10);

    // Get full catalog
    const catalogData = await getProductCatalog();

    // Merge: AI forecasts + static catalog
    const aiProducts = forecastData.products || [];
    const staticProducts = catalogData.products.map((p) => ({
      product_id: p.product_id,
      product_name: p.product_name,
      recommendation: `📦 ${p.stock_status} - View details for restocking`,
      forecast_7d: null, // No AI prediction
      forecast: null,
    }));

    // Combine (AI products first, then catalog)
    const allProducts = [...aiProducts, ...staticProducts];
    setProducts(allProducts);
  } catch (err) {
    setError("Failed to load products");
  } finally {
    setLoading(false);
  }
};
```

**Result:** Shows 10 AI-forecasted products + 50 static catalog items = 60 total

---

## 📊 Recommended Approach for Your Demo

**Use Option 1 + Option 2 Combined:**

1. **Increase frontend limit to 30** (shows all existing products immediately)
2. **Add 2-3 new categories** to mock generator (gaming, wearables, tablets)
3. **Regenerate database** with 60+ products
4. **Update frontend limit to 50**

### Quick Implementation (15 minutes):

```bash
# Step 1: Edit mock generator
# Add gaming, wearables, tablets categories (see Option 2)

# Step 2: Delete old DB
rm ai-core/millionx_ai.db

# Step 3: Regenerate with more products
cd ai-core
python -c "from forecasting import DemandForecaster; import sqlite3; import random; from datetime import datetime, timedelta;

# Create DB and generate 100 sales records instead of 50
conn = sqlite3.connect('millionx_ai.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS sales_history (
  id INTEGER PRIMARY KEY,
  order_id TEXT,
  platform TEXT,
  product_id TEXT,
  product_name TEXT,
  product_category TEXT,
  quantity INTEGER,
  unit_price REAL,
  total_price REAL,
  currency TEXT,
  order_status TEXT,
  payment_method TEXT,
  shipping_region TEXT,
  shipping_city TEXT,
  order_date TEXT,
  ingested_at TEXT
)''')

# Insert 100 records with varied products
products = [
  ('PROD-001', 'iPhone 15 Pro', 'smartphone'),
  ('PROD-002', 'MacBook Pro M3', 'laptop'),
  ('PROD-003', 'Apple Watch 9', 'wearables'),
  ('PROD-004', 'iPad Pro', 'tablet'),
  ('PROD-005', 'PS5 Console', 'gaming'),
  # ... add 45 more
]

for i in range(100):
  product = random.choice(products)
  cursor.execute('''INSERT INTO sales_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
    i, f'ORD-{i}', 'shopify', product[0], product[1], product[2],
    random.randint(1, 5), random.randint(5000, 50000), 0, 'BDT',
    'completed', 'COD', 'Dhaka', 'Dhaka',
    (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
    datetime.now().isoformat()
  ))
conn.commit()
print('✅ Generated 100 sales records')
"

# Step 4: Update frontend limit
cd ../frontend/src/components
# Edit CommandCenter.jsx line ~30: getInventoryForecast(50)

# Step 5: Restart services
cd ../../..
docker-compose restart fastapi
cd frontend
npm run dev
```

---

## 🔍 Verify Your Changes

```bash
# Check database
python check_db.py

# Should show:
# - Total sales records: 100
# - Available Products (50+)

# Test API
curl http://localhost:8000/api/v1/inventory/forecast?limit=50

# Should return 50 products with forecasts
```

---

## 💡 Key Takeaways

1. **Current products** = 30 from SQLite (generated by mock script)
2. **To add more**: Either increase limit OR regenerate database with more categories
3. **Best for demo**: Option 1 + 2 (increase limit + add categories) = 60 products in 15 mins
4. **For production**: Option 3 (hybrid AI + static catalog) for unlimited products

Choose based on your time budget! 🚀
