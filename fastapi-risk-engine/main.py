from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(
    title="COD Shield API",
    description="Real-time fraud detection for Cash-on-Delivery orders",
    version="1.0.0"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
