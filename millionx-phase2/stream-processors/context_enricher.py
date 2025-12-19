"""
Context Enrichment Stream Processor
Enriches social and market data with additional context

Features:
- Product metadata enrichment (category, pricing trends, reviews)
- Weather data integration (location-based context)
- Geographic context (region, city, timezone)
- Trend signals (viral products, seasonal patterns)
- Redis caching for performance

Target Latency: <20ms per message (with cache hits <5ms)
"""

import faust
import redis
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import logging
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.faust_config import (
    get_faust_app_config,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
    WEATHER_API_KEY,
    WEATHER_API_URL,
    validate_config
)
from shared.metrics import (
    record_message_processed,
    measure_latency,
    record_error,
    record_dlq_sent,
    log_metrics_summary
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faust app
app = faust.App(**get_faust_app_config('context-enricher'))

# Redis client for caching
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5
)

# Input topics (anonymized data from Privacy Shield)
input_social_topic = app.topic('enriched.social.anonymized', value_type=bytes)
input_market_topic = app.topic('enriched.market.anonymized', value_type=bytes)

# Output topics (enriched data)
output_social_topic = app.topic('enriched.social.contextualized', value_type=bytes)
output_market_topic = app.topic('enriched.market.contextualized', value_type=bytes)

# Dead Letter Queue
dlq_topic = app.topic('dead-letters-context-enricher', value_type=bytes)

# Cache TTL settings (in seconds)
PRODUCT_METADATA_TTL = 3600  # 1 hour
WEATHER_DATA_TTL = 1800  # 30 minutes
GEO_CONTEXT_TTL = 86400  # 24 hours

# Product category mapping (expandable via database)
PRODUCT_CATEGORIES = {
    'smartphone': ['phone', 'mobile', 'android', 'iphone', 'samsung', 'xiaomi'],
    'laptop': ['laptop', 'macbook', 'notebook', 'chromebook', 'thinkpad'],
    'fashion': ['dress', 'shirt', 'jeans', 'shoes', 'sneakers', 'jacket'],
    'electronics': ['tv', 'headphones', 'speaker', 'camera', 'watch'],
    'home': ['furniture', 'kitchen', 'appliance', 'decor', 'bedding'],
}

# Bangladesh cities (for weather enrichment)
BD_CITIES = {
    'dhaka': {'lat': 23.8103, 'lon': 90.4125},
    'chittagong': {'lat': 22.3569, 'lon': 91.7832},
    'sylhet': {'lat': 24.8949, 'lon': 91.8687},
    'rajshahi': {'lat': 24.3745, 'lon': 88.6042},
    'khulna': {'lat': 22.8456, 'lon': 89.5403},
}


def get_cached_data(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get data from Redis cache"""
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")
    return None


def set_cached_data(cache_key: str, data: Dict[str, Any], ttl: int):
    """Set data in Redis cache"""
    try:
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")


def extract_product_category(text: str) -> Optional[str]:
    """
    Extract product category from text (post content or product name)
    
    Args:
        text: Text to analyze
    
    Returns:
        Category name or None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    for category, keywords in PRODUCT_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return 'general'


async def fetch_weather_data(city: str) -> Optional[Dict[str, Any]]:
    """
    Fetch weather data from OpenWeatherMap API
    
    Args:
        city: City name (must be in BD_CITIES)
    
    Returns:
        Weather data dictionary or None
    """
    if not WEATHER_API_KEY:
        logger.warning("Weather API key not configured. Skipping weather enrichment.")
        return None
    
    city_lower = city.lower()
    if city_lower not in BD_CITIES:
        logger.debug(f"City {city} not in supported list. Skipping weather enrichment.")
        return None
    
    # Check cache first
    cache_key = f"weather:{city_lower}"
    cached = get_cached_data(cache_key)
    if cached:
        logger.debug(f"Weather cache hit for {city}")
        return cached
    
    # Fetch from API
    coords = BD_CITIES[city_lower]
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{WEATHER_API_URL}?lat={coords['lat']}&lon={coords['lon']}&appid={WEATHER_API_KEY}&units=metric"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    weather_context = {
                        'city': city,
                        'temperature': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'conditions': data['weather'][0]['main'],
                        'description': data['weather'][0]['description'],
                        'wind_speed': data['wind']['speed'],
                        'is_extreme_weather': data['main']['temp'] > 38 or data['main']['temp'] < 10,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Cache the result
                    set_cached_data(cache_key, weather_context, WEATHER_DATA_TTL)
                    
                    return weather_context
                else:
                    logger.warning(f"Weather API returned status {response.status}")
                    return None
    
    except asyncio.TimeoutError:
        logger.warning(f"Weather API timeout for {city}")
        return None
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None


def enrich_with_product_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich record with product category and metadata
    
    Args:
        record: Data record
    
    Returns:
        Enriched record with product metadata
    """
    enriched = record.copy()
    
    # Extract product mentions from content
    content = record.get('content', '') or record.get('product_name', '')
    
    if content:
        category = extract_product_category(content)
        
        enriched['context'] = enriched.get('context', {})
        enriched['context']['product_category'] = category
        enriched['context']['category_confidence'] = 0.8  # Placeholder (use ML model in production)
    
    return enriched


async def enrich_with_weather_context(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich record with weather data based on location
    
    Args:
        record: Data record
    
    Returns:
        Enriched record with weather context
    """
    enriched = record.copy()
    
    # Try to extract location from various fields
    location = (
        record.get('location') or
        record.get('region') or
        record.get('city') or
        record.get('shipping_region')
    )
    
    if location:
        weather_data = await fetch_weather_data(location)
        
        if weather_data:
            enriched['context'] = enriched.get('context', {})
            enriched['context']['weather'] = weather_data
    
    return enriched


def enrich_with_temporal_context(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add temporal context (time of day, day of week, season)
    
    Args:
        record: Data record
    
    Returns:
        Enriched record with temporal context
    """
    enriched = record.copy()
    
    # Use posted_at or created_at timestamp
    timestamp_str = record.get('posted_at') or record.get('created_at')
    
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            enriched['context'] = enriched.get('context', {})
            enriched['context']['temporal'] = {
                'hour': timestamp.hour,
                'day_of_week': timestamp.strftime('%A'),
                'is_weekend': timestamp.weekday() >= 5,
                'is_business_hours': 9 <= timestamp.hour <= 17,
                'season': get_season(timestamp.month)
            }
        except Exception as e:
            logger.warning(f"Failed to parse timestamp: {e}")
    
    return enriched


def get_season(month: int) -> str:
    """Get season based on month (Bangladesh climate)"""
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'summer'
    elif month in [6, 7, 8]:
        return 'monsoon'
    else:
        return 'autumn'


@app.agent(input_social_topic)
@measure_latency('context_enricher_social')
async def enrich_social(stream):
    """Enrich social media posts with context"""
    async for key, raw_message in stream.items():
        try:
            message = json.loads(raw_message.decode('utf-8'))
            
            # Apply enrichments
            enriched = enrich_with_product_metadata(message)
            enriched = await enrich_with_weather_context(enriched)
            enriched = enrich_with_temporal_context(enriched)
            
            # Add enrichment metadata
            enriched['_enriched'] = True
            enriched['_enrichment_timestamp'] = datetime.utcnow().isoformat()
            
            # Send to output topic
            await output_social_topic.send(
                key=key,
                value=json.dumps(enriched).encode('utf-8')
            )
            
            record_message_processed('context_enricher', 'enriched.social.anonymized')
            logger.debug(f"✅ Enriched social post: {message.get('post_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error enriching social post: {e}", exc_info=True)
            record_error('context_enricher_social', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('context_enricher', 'dead-letters-context-enricher')


@app.agent(input_market_topic)
@measure_latency('context_enricher_market')
async def enrich_market(stream):
    """Enrich market orders with context"""
    async for key, raw_message in stream.items():
        try:
            message = json.loads(raw_message.decode('utf-8'))
            
            # Apply enrichments
            enriched = enrich_with_product_metadata(message)
            enriched = await enrich_with_weather_context(enriched)
            enriched = enrich_with_temporal_context(enriched)
            
            # Add enrichment metadata
            enriched['_enriched'] = True
            enriched['_enrichment_timestamp'] = datetime.utcnow().isoformat()
            
            # Send to output topic
            await output_market_topic.send(
                key=key,
                value=json.dumps(enriched).encode('utf-8')
            )
            
            record_message_processed('context_enricher', 'enriched.market.anonymized')
            logger.debug(f"✅ Enriched market order: {message.get('order_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error enriching market order: {e}", exc_info=True)
            record_error('context_enricher_market', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('context_enricher', 'dead-letters-context-enricher')


@app.timer(interval=60.0)
async def log_metrics():
    """Log metrics every 60 seconds"""
    log_metrics_summary()


@app.on_started.connect
async def on_started(app, **kwargs):
    """Log startup message and validate configuration"""
    logger.info("🌍 Context Enricher started successfully!")
    logger.info(f"  Input topics: enriched.social.anonymized, enriched.market.anonymized")
    logger.info(f"  Output topics: enriched.social.contextualized, enriched.market.contextualized")
    logger.info(f"  Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"  Weather API: {'Enabled' if WEATHER_API_KEY else 'Disabled'}")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Validate configuration
    validation_errors = validate_config()
    if validation_errors:
        for error in validation_errors:
            logger.warning(error)


if __name__ == '__main__':
    app.main()
