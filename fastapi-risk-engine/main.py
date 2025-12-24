from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import time
from datetime import datetime
import sys

# Load environment variables
load_dotenv()

# Ensure we can import from ai-core (mapped via Docker volume)
sys.path.append('/ai-core')

try:
    from agent_workflow import InventoryCopilot
    copilot = InventoryCopilot()
    ai_available = True
    print("✅ AI Core loaded successfully")
except ImportError as e:
    print(f"⚠️ AI Core not found: {e}")
    ai_available = False

# Import Phase 2 enhanced modules
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai-core'))
    from forecasting_enhanced import EnhancedDemandForecaster
    from sentiment import analyze_sentiment, batch_analyze_sentiments
    from graph_analytics import ProductGraphAnalytics
    
    forecaster = EnhancedDemandForecaster()
    graph_analytics = ProductGraphAnalytics()
    phase2_available = True
    print("✅ Phase 2 modules loaded (VADER, statsforecast, NetworkX)")
except ImportError as e:
    print(f"⚠️ Phase 2 modules not found: {e}")
    phase2_available = False
    forecaster = None
    graph_analytics = None

# Import Phase 3 Haggling Engine
try:
    from haggling_engine import (
        PriceShiftEngine, HagglingTwin,
        get_optimal_price, run_negotiation_simulation, get_counter_offer
    )
    price_shift_engine = PriceShiftEngine()
    haggling_twin = HagglingTwin()
    phase3_available = True
    print("✅ Phase 3 modules loaded (PriceShift, Haggling Twin)")
except ImportError as e:
    print(f"⚠️ Phase 3 modules not found: {e}")
    phase3_available = False
    price_shift_engine = None
    haggling_twin = None

app = FastAPI(
    title="MillionX API",
    description="COD Shield + Inventory Copilot AI",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', ''),
    decode_responses=True
)

# Data Models
class DeliveryAddress(BaseModel):
    area: str
    city: str
    postal_code: str

class OrderDetails(BaseModel):
    total_amount: float
    currency: str = "BDT"
    items_count: int
    is_first_order: bool

class OrderData(BaseModel):
    order_id: str
    merchant_id: str
    customer_phone: str
    delivery_address: DeliveryAddress
    order_details: OrderDetails
    timestamp: str

class RiskFactor(BaseModel):
    factor: str
    weight: int
    description: str

class RiskResponse(BaseModel):
    order_id: str
    risk_score: int
    risk_level: str
    recommendation: str
    factors: List[RiskFactor]
    suggested_actions: List[str]
    processing_time_ms: int

# Helper Functions
def check_blacklist(phone: str) -> int:
    """Check Redis blacklist for phone number"""
    blacklist_key = f"blacklist:{phone}"
    try:
        hits = redis_client.get(blacklist_key)
        return int(hits) if hits else 0
    except Exception as e:
        print(f"Redis error: {e}")
        return 0

def is_suspicious_time(timestamp_str: str) -> bool:
    """Check if order time is suspicious (2-5 AM)"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        hour = dt.hour
        return 2 <= hour <= 5
    except:
        return False

def calculate_risk_score(order: OrderData) -> tuple:
    """
    Calculate risk score based on multiple factors
    Returns: (risk_score, factors_list)
    """
    risk_score = 0
    factors = []
    
    # Factor 1: Blacklist Check (0-60 points)
    blacklist_hits = check_blacklist(order.customer_phone)
    if blacklist_hits > 0:
        weight = min(blacklist_hits * 30, 60)
        risk_score += weight
        factors.append(RiskFactor(
            factor="BLACKLISTED_PHONE",
            weight=weight,
            description=f"Phone number has {blacklist_hits} previous failed deliveries"
        ))
    
    # Factor 2: First Order + High Value (0-30 points)
    if order.order_details.is_first_order:
        amount = order.order_details.total_amount
        if amount > 1000:
            risk_score += 30
            factors.append(RiskFactor(
                factor="HIGH_VALUE_FIRST_ORDER",
                weight=30,
                description=f"Order amount Tk {amount} for new customer"
            ))
        elif amount > 500:
            risk_score += 15
            factors.append(RiskFactor(
                factor="MEDIUM_VALUE_FIRST_ORDER",
                weight=15,
                description=f"Order amount Tk {amount} for new customer"
            ))
    
    # Factor 3: Address Risk (0-20 points)
    risky_areas = ['Unknown', 'Remote', 'Unspecified', '']
    if order.delivery_address.area in risky_areas:
        risk_score += 20
        factors.append(RiskFactor(
            factor="RISKY_DELIVERY_AREA",
            weight=20,
            description=f"Delivery area '{order.delivery_address.area}' is high-risk"
        ))
    
    # Factor 4: Time Anomaly (0-10 points)
    if is_suspicious_time(order.timestamp):
        risk_score += 10
        factors.append(RiskFactor(
            factor="SUSPICIOUS_ORDER_TIME",
            weight=10,
            description="Order placed during suspicious hours (2-5 AM)"
        ))
    
    return min(risk_score, 100), factors

def get_recommendation(risk_score: int) -> tuple:
    """
    Get recommendation and suggested actions based on risk score
    Returns: (risk_level, recommendation, suggested_actions)
    """
    if risk_score <= 40:
        return (
            "LOW",
            "PROCEED_WITH_COD",
            ["Process order normally", "Standard delivery process"]
        )
    elif risk_score <= 70:
        return (
            "MEDIUM",
            "CONFIRMATION_CALL_REQUIRED",
            [
                "Call customer to confirm order",
                "Verify delivery address",
                "Send SMS confirmation before dispatch"
            ]
        )
    else:
        return (
            "HIGH",
            "ADVANCE_PAYMENT_REQUIRED",
            [
                "Request 50% advance payment via bKash",
                "Limit COD to Tk 500 maximum",
                "Consider rejecting order if customer refuses advance"
            ]
        )

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "COD Shield API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "COD Shield",
        "redis": redis_status
    }

@app.post("/api/v1/risk-score", response_model=RiskResponse)
async def calculate_risk(order: OrderData):
    """
    Calculate risk score for a COD order
    
    - **order_id**: Unique order identifier
    - **customer_phone**: Customer's phone number
    - **delivery_address**: Delivery location details
    - **order_details**: Order amount and items info
    """
    start_time = time.time()
    
    try:
        # Calculate risk score
        risk_score, factors = calculate_risk_score(order)
        
        # Get recommendation
        risk_level, recommendation, actions = get_recommendation(risk_score)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return RiskResponse(
            order_id=order.order_id,
            risk_score=risk_score,
            risk_level=risk_level,
            recommendation=recommendation,
            factors=factors,
            suggested_actions=actions,
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk calculation failed: {str(e)}")

class BlacklistRequest(BaseModel):
    phone: str
    reason: str = "Failed delivery"
    merchant_id: str

@app.post("/api/v1/blacklist/add")
async def add_to_blacklist(request: BlacklistRequest):
    """
    Add a phone number to the blacklist
    
    - **phone**: Phone number to blacklist
    - **reason**: Reason for blacklisting
    - **merchant_id**: ID of merchant reporting
    """
    try:
        blacklist_key = f"blacklist:{request.phone}"
        current_hits = redis_client.get(blacklist_key)
        
        if current_hits:
            new_hits = int(current_hits) + 1
        else:
            new_hits = 1
        
        redis_client.set(blacklist_key, new_hits)
        redis_client.expire(blacklist_key, 86400 * 30)  # 30 days TTL
        
        return {
            "status": "added",
            "phone": request.phone,
            "total_hits": new_hits,
            "reason": request.reason
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blacklist update failed: {str(e)}")

@app.get("/api/v1/inventory/forecast")
async def get_forecast(product_id: str = None, limit: int = 5):
    """
    Get AI-powered inventory forecast and recommendations (Phase 2 Enhanced)
    
    Uses statsforecast AutoARIMA and AutoETS for accurate predictions
    
    - **product_id**: Specific product ID (optional)
    - **limit**: Number of products to forecast in batch mode (default: 5)
    """
    if phase2_available and forecaster:
        try:
            if product_id:
                # Single product forecast with statsforecast
                result = forecaster.predict_demand(product_id=product_id)
                return result
            else:
                # Batch forecast for top products
                results = forecaster.batch_forecast(limit=limit)
                return {
                    "count": len(results),
                    "forecasts": results,
                    "model": "statsforecast (AutoARIMA, AutoETS)",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Phase 2 forecast failed: {str(e)}")
    
    elif ai_available:
        # Fallback to original copilot
        try:
            if product_id:
                result = copilot.process(product_id=product_id)
                return result
            else:
                results = copilot.process_batch(limit=limit)
                return {
                    "count": len(results),
                    "products": results,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")
    
    else:
        return {"error": "AI Core not connected", "recommendation": "Please check ai-core module"}

@app.post("/api/v1/sentiment/analyze")
async def analyze_text_sentiment(texts: List[str]):
    """
    Analyze sentiment of text(s) using VADER (Phase 2)
    
    - **texts**: List of texts to analyze (reviews, comments, feedback)
    """
    if not phase2_available:
        return {"error": "Phase 2 modules not available"}
    
    try:
        results = batch_analyze_sentiments(texts)
        aggregate = {
            "total_texts": len(results),
            "positive": sum(1 for r in results if r['label'] == 'positive'),
            "negative": sum(1 for r in results if r['label'] == 'negative'),
            "neutral": sum(1 for r in results if r['label'] == 'neutral')
        }
        
        return {
            "results": results,
            "aggregate": aggregate,
            "model": "VADER Sentiment Analysis"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@app.get("/api/v1/products/bundles")
async def get_product_bundles(product_id: str, limit: int = 3):
    """
    Get product bundle recommendations using graph analytics (Phase 2)
    
    - **product_id**: Product to find bundles for
    - **limit**: Maximum number of recommendations (default: 3)
    """
    if not phase2_available or not graph_analytics:
        return {"error": "Phase 2 graph analytics not available"}
    
    try:
        bundles = graph_analytics.recommend_bundles(product_id=product_id, limit=limit)
        return {
            "product_id": product_id,
            "recommendations": bundles,
            "model": "NetworkX Graph Analytics"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bundle recommendation failed: {str(e)}")

@app.get("/api/v1/products/centrality")
async def get_product_centrality():
    """
    Get product centrality metrics (importance scores) using graph analytics (Phase 2)
    
    Returns PageRank, Betweenness, Degree centrality for products
    """
    if not phase2_available or not graph_analytics:
        return {"error": "Phase 2 graph analytics not available"}
    
    try:
        centrality = graph_analytics.calculate_product_centrality()
        return {
            "centrality_metrics": centrality,
            "model": "NetworkX Graph Analytics",
            "metrics": ["PageRank", "Betweenness Centrality", "Degree Centrality"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centrality calculation failed: {str(e)}")

@app.get("/api/v1/blacklist/check")
async def check_blacklist_status(phone: str):
    """
    Check if a phone number is blacklisted
    
    - **phone**: Phone number to check (query parameter)
    """
    hits = check_blacklist(phone)
    
    return {
        "phone": phone,
        "is_blacklisted": hits > 0,
        "failed_deliveries": hits,
        "risk_level": "HIGH" if hits >= 2 else "MEDIUM" if hits == 1 else "LOW"
    }


# ============= SMART COPILOT ENDPOINTS =============
# These endpoints power the WhatsApp chatbot with real data

@app.get("/api/v1/merchant/profit")
async def get_merchant_profit(merchant_id: str = "demo", period: str = "month"):
    """
    Get merchant profit summary from sales data (Smart Copilot)
    
    - **merchant_id**: Merchant identifier (default: demo)
    - **period**: Time period - 'week', 'month', or 'year' (default: month)
    """
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    # Determine date range
    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=7)
        period_name = "This Week"
    elif period == "year":
        start_date = now - timedelta(days=365)
        period_name = "This Year"
    else:
        start_date = now - timedelta(days=30)
        period_name = "This Month"
    
    try:
        # Use Phase 2 forecaster's engine for database access
        if phase2_available and forecaster:
            with forecaster.engine.connect() as conn:
                # Get sales summary
                query = text("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_amount) as total_revenue,
                        SUM(quantity) as total_units,
                        AVG(total_amount) as avg_order_value,
                        product_name as top_product,
                        MAX(quantity) as top_quantity
                    FROM sales_history
                    WHERE order_date >= :start_date
                    GROUP BY product_name
                    ORDER BY SUM(quantity) DESC
                    LIMIT 1
                """)
                result = conn.execute(query, {"start_date": start_date.strftime("%Y-%m-%d")})
                row = result.fetchone()
                
                if row:
                    total_revenue = float(row[1]) if row[1] else 0
                    # Estimate costs at 70% of revenue (industry standard)
                    estimated_costs = total_revenue * 0.70
                    net_profit = total_revenue - estimated_costs
                    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
                    
                    # Get trend (compare to previous period)
                    prev_start = start_date - (now - start_date)
                    trend_query = text("""
                        SELECT SUM(total_amount) as prev_revenue
                        FROM sales_history
                        WHERE order_date >= :prev_start AND order_date < :start_date
                    """)
                    trend_result = conn.execute(trend_query, {
                        "prev_start": prev_start.strftime("%Y-%m-%d"),
                        "start_date": start_date.strftime("%Y-%m-%d")
                    })
                    prev_row = trend_result.fetchone()
                    prev_revenue = float(prev_row[0]) if prev_row and prev_row[0] else 0
                    
                    if prev_revenue > 0:
                        growth_pct = ((total_revenue - prev_revenue) / prev_revenue) * 100
                        trend = f"+{growth_pct:.0f}%" if growth_pct > 0 else f"{growth_pct:.0f}%"
                    else:
                        trend = "N/A"
                    
                    return {
                        "period": period_name,
                        "merchant_id": merchant_id,
                        "revenue": round(total_revenue, 2),
                        "estimated_costs": round(estimated_costs, 2),
                        "net_profit": round(net_profit, 2),
                        "profit_margin_pct": round(profit_margin, 1),
                        "total_orders": int(row[0]) if row[0] else 0,
                        "total_units_sold": int(row[2]) if row[2] else 0,
                        "avg_order_value": round(float(row[3]), 2) if row[3] else 0,
                        "top_seller": {
                            "product": row[4] if row[4] else "N/A",
                            "units_sold": int(row[5]) if row[5] else 0
                        },
                        "trend_vs_previous": trend,
                        "currency": "BDT",
                        "generated_at": datetime.now().isoformat()
                    }
        
        # Fallback if no data
        return {
            "period": period_name,
            "merchant_id": merchant_id,
            "revenue": 0,
            "net_profit": 0,
            "message": "No sales data available for this period",
            "currency": "BDT"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profit calculation failed: {str(e)}")


@app.get("/api/v1/merchant/inventory")
async def get_merchant_inventory(merchant_id: str = "demo", threshold: int = 10):
    """
    Get merchant inventory status with low stock alerts (Smart Copilot)
    
    - **merchant_id**: Merchant identifier (default: demo)
    - **threshold**: Low stock threshold (default: 10 units)
    """
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    try:
        if phase2_available and forecaster:
            with forecaster.engine.connect() as conn:
                # Get recent sales velocity by product
                query = text("""
                    SELECT 
                        product_id,
                        product_name,
                        product_category,
                        SUM(quantity) as total_sold,
                        COUNT(*) as order_count,
                        MAX(order_date) as last_sale
                    FROM sales_history
                    WHERE order_date >= :start_date
                    GROUP BY product_id, product_name, product_category
                    ORDER BY SUM(quantity) DESC
                """)
                
                start_date = datetime.now() - timedelta(days=30)
                result = conn.execute(query, {"start_date": start_date.strftime("%Y-%m-%d")})
                rows = result.fetchall()
                
                inventory_items = []
                low_stock_alerts = []
                
                for row in rows:
                    # Simulate stock level based on sales (assume we restock weekly)
                    weekly_sales = int(row[3]) / 4  # 30 days / 4 weeks
                    estimated_stock = max(0, int(50 - int(row[3]) * 0.3))  # Rough estimate
                    days_until_stockout = int(estimated_stock / weekly_sales * 7) if weekly_sales > 0 else 999
                    
                    item = {
                        "product_id": row[0],
                        "product_name": row[1],
                        "category": row[2],
                        "estimated_stock": estimated_stock,
                        "monthly_velocity": int(row[3]),
                        "days_until_stockout": days_until_stockout,
                        "status": "LOW" if estimated_stock < threshold else "NORMAL"
                    }
                    inventory_items.append(item)
                    
                    if estimated_stock < threshold:
                        low_stock_alerts.append({
                            "product_name": row[1],
                            "estimated_stock": estimated_stock,
                            "recommendation": f"Restock soon - selling ~{int(weekly_sales)} per week"
                        })
                
                # Get trending products for tips
                trending = [i for i in inventory_items if i["monthly_velocity"] > 5][:3]
                
                return {
                    "merchant_id": merchant_id,
                    "total_products": len(inventory_items),
                    "low_stock_count": len(low_stock_alerts),
                    "low_stock_alerts": low_stock_alerts[:5],  # Top 5 alerts
                    "trending_products": [t["product_name"] for t in trending],
                    "inventory_summary": inventory_items[:10],  # Top 10 products
                    "tip": f"Restock {low_stock_alerts[0]['product_name']} soon (trending!)" if low_stock_alerts else "All stock levels healthy!",
                    "generated_at": datetime.now().isoformat()
                }
        
        # Fallback
        return {
            "merchant_id": merchant_id,
            "low_stock_alerts": [],
            "message": "No inventory data available",
            "tip": "Start tracking your sales to get inventory insights!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory check failed: {str(e)}")


# ============= PHASE 3: PRICESHIFT & HAGGLING TWIN ENDPOINTS =============

class PriceOptimizationRequest(BaseModel):
    product_id: str
    current_price: float
    cost: float
    category: Optional[str] = None
    strategy: Optional[str] = "balanced"  # aggressive, balanced, conservative

class NegotiationSimRequest(BaseModel):
    product_id: str
    asking_price: float
    cost: float
    num_simulations: Optional[int] = 1000

class CounterOfferRequest(BaseModel):
    asking_price: float
    customer_offer: float
    cost: float
    round_number: Optional[int] = 1

@app.post("/api/v1/price/optimize")
async def optimize_price(request: PriceOptimizationRequest):
    """
    PriceShift: Get optimal price recommendation using demand elasticity
    
    - **product_id**: Product to optimize pricing for
    - **current_price**: Current selling price in BDT
    - **cost**: Product cost in BDT
    - **category**: Product category (Electronics, Fashion, etc.)
    - **strategy**: aggressive, balanced, or conservative
    """
    if not phase3_available:
        return {"error": "Phase 3 Haggling Engine not available"}
    
    try:
        from haggling_engine import PriceStrategy
        
        strategy_map = {
            "aggressive": PriceStrategy.AGGRESSIVE,
            "balanced": PriceStrategy.BALANCED,
            "conservative": PriceStrategy.CONSERVATIVE
        }
        strategy = strategy_map.get(request.strategy, PriceStrategy.BALANCED)
        
        result = price_shift_engine.calculate_optimal_price(
            product_id=request.product_id,
            current_price=request.current_price,
            cost=request.cost,
            category=request.category,
            strategy=strategy
        )
        
        return {
            "success": True,
            **result,
            "model": "PriceShift Elasticity Engine"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price optimization failed: {str(e)}")


@app.post("/api/v1/haggling/simulate")
async def simulate_negotiations(request: NegotiationSimRequest):
    """
    Haggling Twin: Run Monte Carlo simulation for negotiation outcomes
    
    Runs 1000 simulations to predict:
    - Conversion rates at different price points
    - Optimal starting price
    - Expected discount patterns
    - Customer satisfaction
    
    - **product_id**: Product being negotiated
    - **asking_price**: Your starting price in BDT
    - **cost**: Product cost in BDT (for margin calculation)
    - **num_simulations**: Number of simulations (default 1000)
    """
    if not phase3_available:
        return {"error": "Phase 3 Haggling Engine not available"}
    
    try:
        result = haggling_twin.run_simulation(
            product_id=request.product_id,
            asking_price=request.asking_price,
            cost=request.cost,
            num_simulations=request.num_simulations
        )
        
        return {
            "success": True,
            **result,
            "model": "Haggling Twin Monte Carlo Simulator"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.post("/api/v1/haggling/counter-offer")
async def generate_counter_offer(request: CounterOfferRequest):
    """
    Haggling Engine: Generate smart counter-offer for real-time negotiation
    
    Powers natural language negotiation like:
    "Can't do 500, but 520 for two? Deal?"
    
    - **asking_price**: Your original asking price in BDT
    - **customer_offer**: Customer's offer in BDT
    - **cost**: Product cost in BDT
    - **round_number**: Which negotiation round (1, 2, 3...)
    """
    if not phase3_available:
        return {"error": "Phase 3 Haggling Engine not available"}
    
    try:
        result = haggling_twin.generate_counter_offer(
            asking_price=request.asking_price,
            customer_offer=request.customer_offer,
            cost=request.cost,
            round_number=request.round_number
        )
        
        return {
            "success": True,
            **result,
            "model": "Haggling Engine Counter-Offer Generator"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counter-offer generation failed: {str(e)}")


@app.get("/api/v1/price/competitor/{product_id}")
async def get_competitor_pricing(product_id: str):
    """
    Get competitor price analysis for a product
    
    - **product_id**: Product to check competitor prices for
    """
    if not phase3_available:
        return {"error": "Phase 3 modules not available"}
    
    try:
        competitor_price = price_shift_engine.get_competitor_price(product_id)
        season, factor = price_shift_engine.get_seasonal_factor()
        
        return {
            "product_id": product_id,
            "competitor_price": competitor_price,
            "current_season": season,
            "seasonal_factor": factor,
            "note": "Competitor prices are simulated. In production, integrates with Daraz/AliExpress APIs."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitor analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
