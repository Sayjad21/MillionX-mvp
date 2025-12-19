"""
Privacy Shield Stream Processor
Anonymizes PII (Personally Identifiable Information) in real-time

Features:
- Regex-based PII detection (phone, email, names)
- SHA-256 hashing with salt for anonymization
- Preserves data structure and utility
- Routes to downstream topics for storage
- DLQ for processing failures

Target Latency: <5ms per message
"""

import faust
import hashlib
import re
from typing import Dict, Any, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.faust_config import (
    get_faust_app_config,
    PRIVACY_SALT,
    PII_HASH_LENGTH,
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
app = faust.App(**get_faust_app_config('privacy-shield'))

# Input topics (raw data from scrapers)
social_tiktok_topic = app.topic('source.social.tiktok', value_type=bytes)
social_facebook_topic = app.topic('source.social.facebook', value_type=bytes)
market_shopify_topic = app.topic('source.market.shopify', value_type=bytes)
market_daraz_topic = app.topic('source.market.daraz', value_type=bytes)

# Output topics (anonymized data)
anonymized_social_topic = app.topic('enriched.social.anonymized', value_type=bytes)
anonymized_market_topic = app.topic('enriched.market.anonymized', value_type=bytes)

# Dead Letter Queue
dlq_topic = app.topic('dead-letters-privacy-shield', value_type=bytes)

# Regex patterns for PII detection
PHONE_PATTERN = re.compile(
    r'\+?880[0-9]{10}|\b0[0-9]{10}\b|'  # Bangladesh numbers
    r'\+?1[0-9]{10}|\b[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'  # US numbers
)
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)
NAME_PATTERN = re.compile(
    r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Simple heuristic: Capitalized First Last
)

# Bangladesh-specific PII patterns
BD_NID_PATTERN = re.compile(r'\b[0-9]{10,17}\b')  # National ID (10-17 digits)
CREDIT_CARD_PATTERN = re.compile(r'\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b')


def hash_pii(text: str, salt: str = PRIVACY_SALT) -> str:
    """
    Hash PII with SHA-256 for anonymization
    
    Args:
        text: The PII text to hash
        salt: Salt for hashing (should be kept secret)
    
    Returns:
        Hashed string (truncated to PII_HASH_LENGTH)
    """
    hashed = hashlib.sha256((text + salt).encode('utf-8')).hexdigest()
    return hashed[:PII_HASH_LENGTH]


def anonymize_text(text: Optional[str]) -> str:
    """
    Replace PII in text with hashed versions
    
    Args:
        text: Text potentially containing PII
    
    Returns:
        Text with PII replaced by hashes
    """
    if not text or not isinstance(text, str):
        return text or ""
    
    # Replace phone numbers
    text = PHONE_PATTERN.sub(
        lambda m: f"PHONE_{hash_pii(m.group(0))}",
        text
    )
    
    # Replace emails
    text = EMAIL_PATTERN.sub(
        lambda m: f"EMAIL_{hash_pii(m.group(0))}",
        text
    )
    
    # Replace names (conservative approach)
    text = NAME_PATTERN.sub(
        lambda m: f"NAME_{hash_pii(m.group(0))}",
        text
    )
    
    # Replace credit cards
    text = CREDIT_CARD_PATTERN.sub(
        lambda m: f"CC_{hash_pii(m.group(0))}",
        text
    )
    
    # Replace Bangladesh National IDs (if in specific fields)
    # Note: This is conservative to avoid false positives with product IDs
    text = BD_NID_PATTERN.sub(
        lambda m: f"NID_{hash_pii(m.group(0))}" if len(m.group(0)) >= 13 else m.group(0),
        text
    )
    
    return text


def anonymize_record(record: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
    """
    Anonymize specific fields in a record
    
    Args:
        record: Data record dictionary
        sensitive_fields: List of field names to anonymize
    
    Returns:
        Record with sensitive fields anonymized
    """
    anonymized = record.copy()
    
    for field in sensitive_fields:
        if field in anonymized:
            value = anonymized[field]
            
            # Handle nested dictionaries
            if isinstance(value, dict):
                anonymized[field] = anonymize_record(value, list(value.keys()))
            
            # Handle lists
            elif isinstance(value, list):
                anonymized[field] = [
                    anonymize_text(item) if isinstance(item, str) else item
                    for item in value
                ]
            
            # Handle strings
            elif isinstance(value, str):
                # Hash specific fields entirely (email, phone, customer_id)
                if field in ['email', 'phone', 'customer_id', 'author', 'customer_name']:
                    anonymized[field] = hash_pii(value)
                else:
                    # Scan for PII in content fields
                    anonymized[field] = anonymize_text(value)
    
    # Add metadata
    anonymized['_anonymized'] = True
    anonymized['_anonymization_version'] = 'v1.0'
    
    return anonymized


@app.agent(social_tiktok_topic)
@measure_latency('privacy_shield_tiktok')
async def process_social_tiktok(stream):
    """Process and anonymize TikTok posts"""
    async for key, raw_message in stream.items():
        try:
            import json
            message = json.loads(raw_message.decode('utf-8'))
            
            # Fields to anonymize in social posts
            sensitive_fields = [
                'author', 'content', 'post_url', 'hashtags',
                'location', 'author_profile_url'
            ]
            
            anonymized = anonymize_record(message, sensitive_fields)
            
            # Send to output topic
            await anonymized_social_topic.send(
                key=key,
                value=json.dumps(anonymized).encode('utf-8')
            )
            
            record_message_processed('privacy_shield', 'source.social.tiktok')
            logger.debug(f"✅ Anonymized TikTok post: {message.get('post_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing TikTok post: {e}", exc_info=True)
            record_error('privacy_shield_tiktok', type(e).__name__)
            
            # Send to DLQ
            await dlq_topic.send(
                key=key,
                value=raw_message
            )
            record_dlq_sent('privacy_shield', 'dead-letters-privacy-shield')


@app.agent(social_facebook_topic)
@measure_latency('privacy_shield_facebook')
async def process_social_facebook(stream):
    """Process and anonymize Facebook posts"""
    async for key, raw_message in stream.items():
        try:
            import json
            message = json.loads(raw_message.decode('utf-8'))
            
            sensitive_fields = [
                'author', 'content', 'post_url', 'hashtags',
                'location', 'author_profile_url'
            ]
            
            anonymized = anonymize_record(message, sensitive_fields)
            
            await anonymized_social_topic.send(
                key=key,
                value=json.dumps(anonymized).encode('utf-8')
            )
            
            record_message_processed('privacy_shield', 'source.social.facebook')
            logger.debug(f"✅ Anonymized Facebook post: {message.get('post_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing Facebook post: {e}", exc_info=True)
            record_error('privacy_shield_facebook', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('privacy_shield', 'dead-letters-privacy-shield')


@app.agent(market_shopify_topic)
@measure_latency('privacy_shield_shopify')
async def process_market_shopify(stream):
    """Process and anonymize Shopify orders"""
    async for key, raw_message in stream.items():
        try:
            import json
            message = json.loads(raw_message.decode('utf-8'))
            
            # Fields to anonymize in market orders
            sensitive_fields = [
                'customer_id', 'email', 'phone', 'customer_name',
                'shipping_address', 'billing_address', 'payment_method'
            ]
            
            anonymized = anonymize_record(message, sensitive_fields)
            
            await anonymized_market_topic.send(
                key=key,
                value=json.dumps(anonymized).encode('utf-8')
            )
            
            record_message_processed('privacy_shield', 'source.market.shopify')
            logger.debug(f"✅ Anonymized Shopify order: {message.get('order_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing Shopify order: {e}", exc_info=True)
            record_error('privacy_shield_shopify', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('privacy_shield', 'dead-letters-privacy-shield')


@app.agent(market_daraz_topic)
@measure_latency('privacy_shield_daraz')
async def process_market_daraz(stream):
    """Process and anonymize Daraz orders"""
    async for key, raw_message in stream.items():
        try:
            import json
            message = json.loads(raw_message.decode('utf-8'))
            
            sensitive_fields = [
                'customer_id', 'email', 'phone', 'customer_name',
                'shipping_address', 'billing_address', 'payment_method'
            ]
            
            anonymized = anonymize_record(message, sensitive_fields)
            
            await anonymized_market_topic.send(
                key=key,
                value=json.dumps(anonymized).encode('utf-8')
            )
            
            record_message_processed('privacy_shield', 'source.market.daraz')
            logger.debug(f"✅ Anonymized Daraz order: {message.get('order_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing Daraz order: {e}", exc_info=True)
            record_error('privacy_shield_daraz', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('privacy_shield', 'dead-letters-privacy-shield')


@app.timer(interval=60.0)
async def log_metrics():
    """Log metrics every 60 seconds"""
    log_metrics_summary()


@app.on_started.connect
async def on_started(app, **kwargs):
    """Log startup message"""
    logger.info("🛡️  Privacy Shield started successfully!")
    logger.info(f"  Listening to topics: source.social.*, source.market.*")
    logger.info(f"  Output topics: enriched.social.anonymized, enriched.market.anonymized")
    logger.info(f"  DLQ topic: dead-letters-privacy-shield")
    
    # Validate configuration
    validation_errors = validate_config()
    if validation_errors:
        for error in validation_errors:
            logger.warning(error)


if __name__ == '__main__':
    app.main()
