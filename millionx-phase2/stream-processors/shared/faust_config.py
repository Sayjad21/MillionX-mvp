"""
Faust Stream Processing Configuration
Shared configuration for all Faust workers
"""

import os
from typing import List

# Kafka Bootstrap Servers
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    'KAFKA_BOOTSTRAP_SERVERS', 
    'localhost:9092'
).split(',')

# Faust Application Settings
FAUST_BROKER = f"kafka://{','.join(KAFKA_BOOTSTRAP_SERVERS)}"
FAUST_STORE = os.getenv('FAUST_STORE', 'rocksdb://')
FAUST_WEB_ENABLED = os.getenv('FAUST_WEB_ENABLED', 'true').lower() == 'true'
FAUST_WEB_PORT = int(os.getenv('FAUST_WEB_PORT', '6066'))

# Topic Prefixes
SOURCE_TOPIC_PREFIX = 'source.'
ENRICHED_TOPIC_PREFIX = 'enriched.'
SINK_TOPIC_PREFIX = 'sink.'
DLQ_TOPIC_PREFIX = 'dead-letters-'

# Performance Tuning
FAUST_STREAM_BUFFER_MAXSIZE = int(os.getenv('FAUST_STREAM_BUFFER_MAXSIZE', '4096'))
FAUST_STREAM_WAIT_EMPTY = os.getenv('FAUST_STREAM_WAIT_EMPTY', 'true').lower() == 'true'
FAUST_PRODUCER_ACKS = int(os.getenv('FAUST_PRODUCER_ACKS', '-1'))  # all replicas
FAUST_PRODUCER_COMPRESSION = os.getenv('FAUST_PRODUCER_COMPRESSION', 'gzip')

# Privacy Shield Settings
PRIVACY_SALT = os.getenv('PRIVACY_SALT', 'millionx_privacy_salt_2025_CHANGE_IN_PROD')
PII_HASH_LENGTH = int(os.getenv('PII_HASH_LENGTH', '16'))

# Context Enrichment Settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5/weather')

# Embedding Service Settings
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
EMBEDDING_MAX_LENGTH = int(os.getenv('EMBEDDING_MAX_LENGTH', '512'))
EMBEDDING_DEVICE = os.getenv('EMBEDDING_DEVICE', 'cpu')  # cpu or cuda

# Weaviate Settings
WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://localhost:8082')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY', None)

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

def get_faust_app_config(app_name: str, **kwargs) -> dict:
    """
    Generate Faust application configuration
    
    Args:
        app_name: Name of the Faust application
        **kwargs: Additional configuration overrides
    
    Returns:
        Dictionary of Faust configuration
    """
    config = {
        'broker': FAUST_BROKER,
        'store': FAUST_STORE,
        'autodiscover': False,
        'origin': f'millionx.{app_name}',
        'id': app_name,
        'version': 1,
        'broker_credentials': None,  # Add SSL/SASL in production
        'web_enabled': FAUST_WEB_ENABLED,
        'web_port': FAUST_WEB_PORT,
        'stream_buffer_maxsize': FAUST_STREAM_BUFFER_MAXSIZE,
        'stream_wait_empty': FAUST_STREAM_WAIT_EMPTY,
        'producer_acks': FAUST_PRODUCER_ACKS,
        'producer_compression_type': FAUST_PRODUCER_COMPRESSION,
        'topic_partitions': 6,  # Default partitions for new topics
        'topic_replication_factor': 1,  # Increase in production cluster
    }
    
    # Apply overrides
    config.update(kwargs)
    
    return config


def validate_config():
    """Validate critical configuration on startup"""
    errors = []
    
    if PRIVACY_SALT == 'millionx_privacy_salt_2025_CHANGE_IN_PROD':
        errors.append("⚠️  WARNING: Using default PRIVACY_SALT! Set custom value in production.")
    
    if not WEATHER_API_KEY and os.getenv('ENABLE_WEATHER_ENRICHMENT', 'true').lower() == 'true':
        errors.append("⚠️  WARNING: WEATHER_API_KEY not set. Weather enrichment will be disabled.")
    
    if not WEAVIATE_URL:
        errors.append("❌ ERROR: WEAVIATE_URL is required for vector storage.")
    
    return errors


if __name__ == '__main__':
    print("🔧 Faust Configuration")
    print(f"Kafka Brokers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Weaviate: {WEAVIATE_URL}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Embedding Device: {EMBEDDING_DEVICE}")
    
    validation_errors = validate_config()
    if validation_errors:
        print("\n⚠️  Configuration Issues:")
        for error in validation_errors:
            print(f"  {error}")
