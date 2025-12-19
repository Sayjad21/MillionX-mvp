"""
Pydantic Data Models for MillionX Phase 2
Strict schemas for data validation across all sources
"""
from pydantic import BaseModel, Field, validator, field_validator
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms"""
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class MarketPlatform(str, Enum):
    """Supported e-commerce platforms"""
    SHOPIFY = "shopify"
    DARAZ = "daraz"


class SocialPost(BaseModel):
    """Strict schema for social media posts"""
    post_id: str = Field(..., description="Unique platform post ID")
    platform: Platform = Field(..., description="Source platform")
    content: str = Field(..., min_length=1, max_length=10000, description="Post text content")
    author: str = Field(..., description="Username/handle (will be hashed)")
    author_id: Optional[str] = Field(None, description="Author ID if available")
    engagement_count: int = Field(ge=0, description="Total likes + comments + shares")
    likes_count: Optional[int] = Field(None, ge=0)
    comments_count: Optional[int] = Field(None, ge=0)
    shares_count: Optional[int] = Field(None, ge=0)
    views_count: Optional[int] = Field(None, ge=0)
    hashtags: List[str] = Field(default_factory=list, description="Extracted hashtags")
    mentioned_products: List[str] = Field(default_factory=list, description="Product keywords detected")
    post_url: str = Field(..., description="Direct link to post")
    posted_at: datetime = Field(..., description="Original post timestamp")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When we scraped it")
    media_urls: List[str] = Field(default_factory=list, description="Image/video URLs")
    location: Optional[str] = Field(None, description="Geographic location if available")
    language: str = Field(default="en", description="Detected language code")
    
    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content has actual text"""
        if not v or v.strip() == "":
            raise ValueError("Content cannot be empty")
        return v.strip()
    
    @field_validator('hashtags', 'mentioned_products')
    @classmethod
    def lowercase_lists(cls, v: List[str]) -> List[str]:
        """Normalize to lowercase"""
        return [item.lower().strip() for item in v if item.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "tiktok_7312345678901234567",
                "platform": "tiktok",
                "content": "Check out this amazing phone deal! #tech #shopping",
                "author": "tech_reviewer_bd",
                "engagement_count": 1250,
                "likes_count": 1000,
                "comments_count": 200,
                "shares_count": 50,
                "hashtags": ["tech", "shopping"],
                "mentioned_products": ["phone", "smartphone"],
                "post_url": "https://tiktok.com/@user/video/123",
                "posted_at": "2025-12-20T10:30:00Z"
            }
        }


class MarketOrder(BaseModel):
    """Schema for e-commerce orders"""
    order_id: str = Field(..., description="Unique order ID from platform")
    platform: MarketPlatform = Field(..., description="Source e-commerce platform")
    customer_id: str = Field(..., description="Customer identifier (will be hashed)")
    customer_email_hash: Optional[str] = Field(None, description="Pre-hashed email")
    product_id: str = Field(..., description="Product SKU or ID")
    product_name: str = Field(..., min_length=1, max_length=500)
    product_category: Optional[str] = Field(None, description="Product category/tags")
    quantity: int = Field(ge=1, description="Order quantity")
    unit_price: float = Field(ge=0, description="Price per unit in BDT")
    total_price: float = Field(ge=0, description="Total order value")
    currency: str = Field(default="BDT", description="Currency code")
    order_status: Literal["pending", "confirmed", "shipped", "delivered", "cancelled"] = Field(
        ..., description="Current order status"
    )
    payment_method: Optional[str] = Field(None, description="Payment method used")
    shipping_region: Optional[str] = Field(None, description="Dhaka, Chittagong, etc.")
    order_timestamp: datetime = Field(..., description="When order was placed")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('total_price')
    @classmethod
    def validate_total(cls, v: float, info) -> float:
        """Ensure total matches quantity * unit_price"""
        data = info.data
        if 'quantity' in data and 'unit_price' in data:
            expected_total = data['quantity'] * data['unit_price']
            if abs(v - expected_total) > 0.01:  # Allow 0.01 rounding error
                raise ValueError(
                    f"Total price {v} doesn't match quantity * unit_price = {expected_total}"
                )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "SHOP-2025-001234",
                "platform": "shopify",
                "customer_id": "cust_abc123",
                "product_id": "PROD-PHONE-001",
                "product_name": "Samsung Galaxy A54 128GB",
                "product_category": "Electronics > Mobile Phones",
                "quantity": 1,
                "unit_price": 42000.00,
                "total_price": 42000.00,
                "currency": "BDT",
                "order_status": "confirmed",
                "shipping_region": "Dhaka",
                "order_timestamp": "2025-12-20T14:30:00Z"
            }
        }


class WeatherData(BaseModel):
    """Schema for weather/context data"""
    location: str = Field(..., description="City name (Dhaka, Chittagong, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature_celsius: float = Field(..., description="Current temperature")
    humidity_percent: float = Field(ge=0, le=100)
    weather_condition: str = Field(..., description="sunny, rainy, cloudy, etc.")
    is_extreme_weather: bool = Field(default=False, description="Floods, storms, etc.")
    rainfall_mm: Optional[float] = Field(None, ge=0, description="24h rainfall")
    
    @field_validator('temperature_celsius')
    @classmethod
    def reasonable_temperature(cls, v: float) -> float:
        """Sanity check for Bangladesh climate"""
        if v < 10 or v > 45:
            raise ValueError(f"Temperature {v}°C outside reasonable range for Bangladesh")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Dhaka",
                "temperature_celsius": 32.5,
                "humidity_percent": 75,
                "weather_condition": "partly_cloudy",
                "is_extreme_weather": False
            }
        }


class ProductMetadata(BaseModel):
    """Schema for product information (for enrichment)"""
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Brand name")
    price_bdt: float = Field(ge=0, description="Current price in BDT")
    availability: bool = Field(default=True, description="In stock?")
    image_urls: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    average_rating: Optional[float] = Field(None, ge=0, le=5)
    reviews_count: Optional[int] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "PROD-PHONE-001",
                "name": "Samsung Galaxy A54 128GB",
                "description": "Latest Samsung mid-range phone with great camera",
                "category": "Mobile Phones",
                "brand": "Samsung",
                "price_bdt": 42000.00,
                "availability": True,
                "keywords": ["samsung", "galaxy", "smartphone", "5g"],
                "average_rating": 4.5,
                "reviews_count": 1250
            }
        }


# Validation helper functions
def validate_social_post(data: dict) -> tuple[bool, Optional[SocialPost], Optional[str]]:
    """
    Validate social post data against schema
    
    Returns:
        (is_valid, validated_model, error_message)
    """
    try:
        model = SocialPost(**data)
        return True, model, None
    except Exception as e:
        return False, None, str(e)


def validate_market_order(data: dict) -> tuple[bool, Optional[MarketOrder], Optional[str]]:
    """
    Validate market order data against schema
    
    Returns:
        (is_valid, validated_model, error_message)
    """
    try:
        model = MarketOrder(**data)
        return True, model, None
    except Exception as e:
        return False, None, str(e)


# Usage example
if __name__ == "__main__":
    # Test valid social post
    valid_post = {
        "post_id": "test_123",
        "platform": "tiktok",
        "content": "Check out this phone! #tech",
        "author": "test_user",
        "engagement_count": 100,
        "post_url": "https://tiktok.com/test",
        "posted_at": datetime.utcnow().isoformat()
    }
    
    is_valid, model, error = validate_social_post(valid_post)
    if is_valid:
        print(f"✅ Valid post: {model.post_id}")
        print(f"   JSON: {model.model_dump_json(indent=2)}")
    else:
        print(f"❌ Validation error: {error}")
    
    # Test invalid post (missing required field)
    invalid_post = {
        "post_id": "test_456",
        "content": "Missing author field"
    }
    
    is_valid, model, error = validate_social_post(invalid_post)
    if not is_valid:
        print(f"\n❌ Expected validation error: {error}")
