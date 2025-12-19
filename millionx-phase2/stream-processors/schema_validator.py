"""
Schema Validation Stream Processor
Real-time Pydantic validation layer with automatic DLQ routing

Features:
- Validates all incoming data against Pydantic schemas
- Automatic DLQ routing for validation failures
- Metrics collection (success rate, failure types)
- Early detection of data quality issues

Target Latency: <3ms per message
"""

import faust
from typing import Dict, Any, Optional, Tuple
import logging
import sys
import os
from datetime import datetime
import json

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'scrapers'))

from shared.faust_config import (
    get_faust_app_config,
    validate_config
)
from shared.metrics import (
    record_message_processed,
    measure_latency,
    record_error,
    record_dlq_sent,
    log_metrics_summary
)

# Import Pydantic models from scrapers
try:
    from shared.models import SocialPost, MarketOrder
    logger = logging.getLogger(__name__)
    logger.info("✅ Successfully imported Pydantic models from scrapers")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to import Pydantic models: {e}")
    logger.error("Make sure scrapers/shared/models.py is available")
    raise

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Faust app
app = faust.App(**get_faust_app_config('schema-validator'))

# Input topics (raw data from scrapers)
tiktok_topic = app.topic('source.social.tiktok', value_type=bytes)
facebook_topic = app.topic('source.social.facebook', value_type=bytes)
shopify_topic = app.topic('source.market.shopify', value_type=bytes)
daraz_topic = app.topic('source.market.daraz', value_type=bytes)

# Output topics (validated data - passes through to Privacy Shield)
# Note: This processor validates BEFORE privacy shield processing
validated_tiktok_topic = app.topic('validated.social.tiktok', value_type=bytes)
validated_facebook_topic = app.topic('validated.social.facebook', value_type=bytes)
validated_shopify_topic = app.topic('validated.market.shopify', value_type=bytes)
validated_daraz_topic = app.topic('validated.market.daraz', value_type=bytes)

# Dead Letter Queue for schema validation failures
dlq_topic = app.topic('schema-validation-errors', value_type=bytes)

# Validation statistics
validation_stats = {
    'total_validated': 0,
    'total_passed': 0,
    'total_failed': 0,
    'failure_types': {}
}


def validate_social_post(data: Dict[str, Any]) -> Tuple[bool, Optional[SocialPost], Optional[str]]:
    """
    Validate social post data against Pydantic schema
    
    Args:
        data: Raw data dictionary
    
    Returns:
        Tuple of (is_valid, validated_model, error_message)
    """
    try:
        validated = SocialPost(**data)
        return True, validated, None
    except Exception as e:
        return False, None, str(e)


def validate_market_order(data: Dict[str, Any]) -> Tuple[bool, Optional[MarketOrder], Optional[str]]:
    """
    Validate market order data against Pydantic schema
    
    Args:
        data: Raw data dictionary
    
    Returns:
        Tuple of (is_valid, validated_model, error_message)
    """
    try:
        validated = MarketOrder(**data)
        return True, validated, None
    except Exception as e:
        return False, None, str(e)


async def handle_validation_failure(
    key: str,
    raw_message: bytes,
    data: Dict[str, Any],
    error: str,
    source_topic: str
):
    """
    Handle validation failure by sending to DLQ with metadata
    
    Args:
        key: Message key
        raw_message: Original raw message
        data: Parsed data (may be incomplete)
        error: Validation error message
        source_topic: Original topic name
    """
    dlq_message = {
        'original_data': data,
        'error': {
            'type': 'ValidationError',
            'message': error,
            'timestamp': datetime.utcnow().isoformat()
        },
        'metadata': {
            'source_topic': source_topic,
            'processor': 'schema-validator',
            'retry_count': 0
        }
    }
    
    await dlq_topic.send(
        key=key,
        value=json.dumps(dlq_message).encode('utf-8')
    )
    
    # Update statistics
    validation_stats['total_failed'] += 1
    
    # Track failure types
    error_type = error.split(':')[0] if ':' in error else 'Unknown'
    validation_stats['failure_types'][error_type] = \
        validation_stats['failure_types'].get(error_type, 0) + 1
    
    record_dlq_sent('schema_validator', 'schema-validation-errors')
    logger.warning(f"⚠️  Validation failed for {source_topic}: {error}")


@app.agent(tiktok_topic)
@measure_latency('schema_validator_tiktok')
async def validate_tiktok(stream):
    """Validate TikTok posts"""
    async for key, raw_message in stream.items():
        try:
            data = json.loads(raw_message.decode('utf-8'))
            
            # Validate against schema
            is_valid, validated_model, error = validate_social_post(data)
            
            validation_stats['total_validated'] += 1
            
            if is_valid:
                # Pass validated data downstream
                await validated_tiktok_topic.send(
                    key=key,
                    value=raw_message  # Keep original message
                )
                
                validation_stats['total_passed'] += 1
                record_message_processed('schema_validator', 'source.social.tiktok')
                logger.debug(f"✅ Validated TikTok post: {data.get('post_id', 'unknown')}")
            else:
                # Send to DLQ
                await handle_validation_failure(
                    key, raw_message, data, error, 'source.social.tiktok'
                )
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in TikTok message: {e}")
            record_error('schema_validator_tiktok', 'JSONDecodeError')
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('schema_validator', 'schema-validation-errors')
        
        except Exception as e:
            logger.error(f"❌ Unexpected error validating TikTok post: {e}", exc_info=True)
            record_error('schema_validator_tiktok', type(e).__name__)


@app.agent(facebook_topic)
@measure_latency('schema_validator_facebook')
async def validate_facebook(stream):
    """Validate Facebook posts"""
    async for key, raw_message in stream.items():
        try:
            data = json.loads(raw_message.decode('utf-8'))
            
            is_valid, validated_model, error = validate_social_post(data)
            
            validation_stats['total_validated'] += 1
            
            if is_valid:
                await validated_facebook_topic.send(key=key, value=raw_message)
                validation_stats['total_passed'] += 1
                record_message_processed('schema_validator', 'source.social.facebook')
                logger.debug(f"✅ Validated Facebook post: {data.get('post_id', 'unknown')}")
            else:
                await handle_validation_failure(
                    key, raw_message, data, error, 'source.social.facebook'
                )
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in Facebook message: {e}")
            record_error('schema_validator_facebook', 'JSONDecodeError')
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('schema_validator', 'schema-validation-errors')
        
        except Exception as e:
            logger.error(f"❌ Unexpected error validating Facebook post: {e}", exc_info=True)
            record_error('schema_validator_facebook', type(e).__name__)


@app.agent(shopify_topic)
@measure_latency('schema_validator_shopify')
async def validate_shopify(stream):
    """Validate Shopify orders"""
    async for key, raw_message in stream.items():
        try:
            data = json.loads(raw_message.decode('utf-8'))
            
            is_valid, validated_model, error = validate_market_order(data)
            
            validation_stats['total_validated'] += 1
            
            if is_valid:
                await validated_shopify_topic.send(key=key, value=raw_message)
                validation_stats['total_passed'] += 1
                record_message_processed('schema_validator', 'source.market.shopify')
                logger.debug(f"✅ Validated Shopify order: {data.get('order_id', 'unknown')}")
            else:
                await handle_validation_failure(
                    key, raw_message, data, error, 'source.market.shopify'
                )
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in Shopify message: {e}")
            record_error('schema_validator_shopify', 'JSONDecodeError')
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('schema_validator', 'schema-validation-errors')
        
        except Exception as e:
            logger.error(f"❌ Unexpected error validating Shopify order: {e}", exc_info=True)
            record_error('schema_validator_shopify', type(e).__name__)


@app.agent(daraz_topic)
@measure_latency('schema_validator_daraz')
async def validate_daraz(stream):
    """Validate Daraz orders"""
    async for key, raw_message in stream.items():
        try:
            data = json.loads(raw_message.decode('utf-8'))
            
            is_valid, validated_model, error = validate_market_order(data)
            
            validation_stats['total_validated'] += 1
            
            if is_valid:
                await validated_daraz_topic.send(key=key, value=raw_message)
                validation_stats['total_passed'] += 1
                record_message_processed('schema_validator', 'source.market.daraz')
                logger.debug(f"✅ Validated Daraz order: {data.get('order_id', 'unknown')}")
            else:
                await handle_validation_failure(
                    key, raw_message, data, error, 'source.market.daraz'
                )
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in Daraz message: {e}")
            record_error('schema_validator_daraz', 'JSONDecodeError')
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('schema_validator', 'schema-validation-errors')
        
        except Exception as e:
            logger.error(f"❌ Unexpected error validating Daraz order: {e}", exc_info=True)
            record_error('schema_validator_daraz', type(e).__name__)


@app.timer(interval=60.0)
async def log_validation_stats():
    """Log validation statistics every 60 seconds"""
    logger.info("📊 Validation Statistics:")
    logger.info(f"  Total Validated: {validation_stats['total_validated']}")
    logger.info(f"  Total Passed: {validation_stats['total_passed']}")
    logger.info(f"  Total Failed: {validation_stats['total_failed']}")
    
    if validation_stats['total_validated'] > 0:
        pass_rate = (validation_stats['total_passed'] / validation_stats['total_validated']) * 100
        logger.info(f"  Pass Rate: {pass_rate:.2f}%")
    
    if validation_stats['failure_types']:
        logger.info("  Failure Types:")
        for failure_type, count in validation_stats['failure_types'].items():
            logger.info(f"    {failure_type}: {count}")
    
    log_metrics_summary()


@app.on_started.connect
async def on_started(app, **kwargs):
    """Log startup message"""
    logger.info("✅ Schema Validator started successfully!")
    logger.info(f"  Input topics: source.social.*, source.market.*")
    logger.info(f"  Output topics: validated.social.*, validated.market.*")
    logger.info(f"  DLQ topic: schema-validation-errors")
    logger.info(f"  Validation schemas: SocialPost, MarketOrder")
    
    # Validate configuration
    validation_errors = validate_config()
    if validation_errors:
        for error in validation_errors:
            logger.warning(error)


if __name__ == '__main__':
    app.main()
