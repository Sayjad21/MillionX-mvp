"""
Embedding Service Stream Processor
Generates vector embeddings for semantic search and recommendations

Features:
- Sentence-Transformers for text embedding
- Batch processing for efficiency
- GPU acceleration support
- Pushes vectors to Weaviate vector database
- Handles content from social posts and product descriptions

Target Latency: <100ms P95 (batch processing)
"""

import faust
import weaviate
from sentence_transformers import SentenceTransformer
import torch
from typing import Dict, Any, List, Optional
import logging
import sys
import os
from datetime import datetime
import json
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.faust_config import (
    get_faust_app_config,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MAX_LENGTH,
    EMBEDDING_DEVICE,
    WEAVIATE_URL,
    WEAVIATE_API_KEY,
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
app = faust.App(**get_faust_app_config('embedding-service'))

# Sentence-Transformers model (384-dimensional embeddings)
logger.info(f"Loading embedding model: {EMBEDDING_MODEL} on device: {EMBEDDING_DEVICE}")
try:
    model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    logger.info(f"✅ Model loaded successfully. Embedding dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    logger.error(f"❌ Failed to load embedding model: {e}")
    raise

# Weaviate client
try:
    if WEAVIATE_API_KEY:
        weaviate_client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY)
        )
    else:
        weaviate_client = weaviate.Client(url=WEAVIATE_URL)
    
    logger.info(f"✅ Weaviate client initialized: {WEAVIATE_URL}")
except Exception as e:
    logger.error(f"❌ Failed to initialize Weaviate client: {e}")
    raise

# Input topics (contextualized data)
input_social_topic = app.topic('enriched.social.contextualized', value_type=bytes)
input_market_topic = app.topic('enriched.market.contextualized', value_type=bytes)

# Output topics (for Snowflake archival)
output_social_topic = app.topic('sink.snowflake.social', value_type=bytes)
output_market_topic = app.topic('sink.snowflake.market', value_type=bytes)

# Dead Letter Queue
dlq_topic = app.topic('dead-letters-embedding-service', value_type=bytes)

# Batch buffer for efficient processing
social_batch: List[Dict[str, Any]] = []
market_batch: List[Dict[str, Any]] = []


def extract_embedding_text(record: Dict[str, Any]) -> str:
    """
    Extract relevant text for embedding generation
    
    Args:
        record: Data record
    
    Returns:
        Concatenated text for embedding
    """
    parts = []
    
    # For social posts
    if 'content' in record:
        parts.append(record['content'])
    
    if 'hashtags' in record and isinstance(record['hashtags'], list):
        parts.append(' '.join(record['hashtags']))
    
    # For market orders
    if 'product_name' in record:
        parts.append(record['product_name'])
    
    if 'category' in record:
        parts.append(record['category'])
    
    # Add context if available
    if 'context' in record and isinstance(record['context'], dict):
        if 'product_category' in record['context']:
            parts.append(record['context']['product_category'])
    
    # Combine and truncate
    text = ' '.join(filter(None, parts))
    
    # Truncate to max length (rough estimate: 1 token ≈ 4 chars)
    max_chars = EMBEDDING_MAX_LENGTH * 4
    if len(text) > max_chars:
        text = text[:max_chars]
    
    return text


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts
    
    Args:
        texts: List of texts to embed
    
    Returns:
        List of embedding vectors
    """
    try:
        # Generate embeddings (returns numpy array)
        embeddings = model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convert to list of lists for JSON serialization
        return embeddings.tolist()
    
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        raise


def store_in_weaviate(record: Dict[str, Any], embedding: List[float], collection_name: str) -> bool:
    """
    Store record and embedding in Weaviate
    
    Args:
        record: Data record
        embedding: Vector embedding
        collection_name: Weaviate collection name (SocialPost or MarketOrder)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data object
        data_object = {
            'post_id': record.get('post_id') or record.get('order_id'),
            'platform': record.get('platform', 'unknown'),
            'content': record.get('content') or record.get('product_name'),
            'engagement_count': record.get('engagement_count', 0),
            'posted_at': record.get('posted_at') or record.get('created_at'),
            'product_category': record.get('context', {}).get('product_category'),
            'raw_data': json.dumps(record)  # Store full record as JSON
        }
        
        # Create object in Weaviate
        weaviate_client.data_object.create(
            data_object=data_object,
            class_name=collection_name,
            vector=embedding
        )
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to store in Weaviate: {e}")
        return False


async def process_batch(batch: List[Dict[str, Any]], output_topic, collection_name: str):
    """
    Process a batch of records: generate embeddings and store
    
    Args:
        batch: List of records to process
        output_topic: Kafka topic for archival
        collection_name: Weaviate collection name
    """
    if not batch:
        return
    
    try:
        # Extract texts for embedding
        texts = [extract_embedding_text(record) for record in batch]
        
        # Generate embeddings in batch
        embeddings = generate_embeddings_batch(texts)
        
        # Store each record with its embedding
        for record, embedding in zip(batch, embeddings):
            # Add embedding to record
            record['embedding'] = embedding
            record['_embedding_model'] = EMBEDDING_MODEL
            record['_embedding_timestamp'] = datetime.utcnow().isoformat()
            
            # Store in Weaviate
            success = store_in_weaviate(record, embedding, collection_name)
            
            if success:
                # Send to Snowflake archival topic
                await output_topic.send(
                    key=record.get('post_id') or record.get('order_id'),
                    value=json.dumps(record).encode('utf-8')
                )
                
                record_message_processed('embedding_service', f'batch_{collection_name}')
                logger.debug(f"✅ Embedded and stored: {record.get('post_id') or record.get('order_id')}")
            else:
                logger.warning(f"⚠️  Failed to store in Weaviate: {record.get('post_id') or record.get('order_id')}")
    
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e}", exc_info=True)
        record_error('embedding_service_batch', type(e).__name__)


@app.agent(input_social_topic)
@measure_latency('embedding_service_social')
async def process_social(stream):
    """Process social posts and generate embeddings"""
    global social_batch
    
    async for key, raw_message in stream.items():
        try:
            message = json.loads(raw_message.decode('utf-8'))
            
            # Add to batch
            social_batch.append(message)
            
            # Process batch when it reaches target size
            if len(social_batch) >= EMBEDDING_BATCH_SIZE:
                await process_batch(social_batch, output_social_topic, 'SocialPost')
                social_batch = []
        
        except Exception as e:
            logger.error(f"❌ Error processing social post: {e}", exc_info=True)
            record_error('embedding_service_social', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('embedding_service', 'dead-letters-embedding-service')


@app.agent(input_market_topic)
@measure_latency('embedding_service_market')
async def process_market(stream):
    """Process market orders and generate embeddings"""
    global market_batch
    
    async for key, raw_message in stream.items():
        try:
            message = json.loads(raw_message.decode('utf-8'))
            
            # Add to batch
            market_batch.append(message)
            
            # Process batch when it reaches target size
            if len(market_batch) >= EMBEDDING_BATCH_SIZE:
                await process_batch(market_batch, output_market_topic, 'MarketOrder')
                market_batch = []
        
        except Exception as e:
            logger.error(f"❌ Error processing market order: {e}", exc_info=True)
            record_error('embedding_service_market', type(e).__name__)
            
            await dlq_topic.send(key=key, value=raw_message)
            record_dlq_sent('embedding_service', 'dead-letters-embedding-service')


@app.timer(interval=30.0)
async def flush_batches():
    """Flush remaining batches every 30 seconds"""
    global social_batch, market_batch
    
    if social_batch:
        logger.info(f"⏰ Flushing {len(social_batch)} social posts from batch")
        await process_batch(social_batch, output_social_topic, 'SocialPost')
        social_batch = []
    
    if market_batch:
        logger.info(f"⏰ Flushing {len(market_batch)} market orders from batch")
        await process_batch(market_batch, output_market_topic, 'MarketOrder')
        market_batch = []


@app.timer(interval=60.0)
async def log_metrics():
    """Log metrics every 60 seconds"""
    log_metrics_summary()


@app.on_started.connect
async def on_started(app, **kwargs):
    """Log startup message and validate configuration"""
    logger.info("🧠 Embedding Service started successfully!")
    logger.info(f"  Model: {EMBEDDING_MODEL}")
    logger.info(f"  Device: {EMBEDDING_DEVICE}")
    logger.info(f"  Batch Size: {EMBEDDING_BATCH_SIZE}")
    logger.info(f"  Embedding Dimension: {model.get_sentence_embedding_dimension()}")
    logger.info(f"  Input topics: enriched.social.contextualized, enriched.market.contextualized")
    logger.info(f"  Output topics: sink.snowflake.social, sink.snowflake.market")
    logger.info(f"  Weaviate: {WEAVIATE_URL}")
    
    # Test Weaviate connection
    try:
        weaviate_client.schema.get()
        logger.info("✅ Weaviate connection successful")
    except Exception as e:
        logger.error(f"❌ Weaviate connection failed: {e}")
    
    # Validate configuration
    validation_errors = validate_config()
    if validation_errors:
        for error in validation_errors:
            logger.warning(error)


if __name__ == '__main__':
    app.main()
