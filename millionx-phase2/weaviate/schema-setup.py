"""
Weaviate Schema Setup for MillionX Phase 2

This script initializes Weaviate collections for storing social posts and market orders
with their embeddings. Designed to work with the Embedding Service (Week 3).

Collections:
- SocialPost: Social media content with product analysis
- MarketOrder: E-commerce orders with customer behavior

Author: MillionX Team
Version: 1.0.0
"""

import weaviate
from weaviate.classes.config import Configure, Property, DataType
import os
import sys
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeaviateSchemaManager:
    """Manages Weaviate schema initialization and updates"""
    
    def __init__(self):
        """Initialize connection to Weaviate"""
        self.weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        self.weaviate_api_key = os.getenv('WEAVIATE_API_KEY', '')
        
        try:
            # Connect to Weaviate
            if self.weaviate_api_key:
                self.client = weaviate.Client(
                    url=self.weaviate_url,
                    auth_client_secret=weaviate.AuthApiKey(api_key=self.weaviate_api_key)
                )
            else:
                self.client = weaviate.Client(url=self.weaviate_url)
            
            # Test connection
            if self.client.is_ready():
                logger.info(f"Connected to Weaviate at {self.weaviate_url}")
            else:
                raise ConnectionError("Weaviate is not ready")
                
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    def delete_existing_collections(self):
        """Delete existing collections (use with caution!)"""
        collections = ['SocialPost', 'MarketOrder']
        
        for collection in collections:
            try:
                if self.client.schema.exists(collection):
                    self.client.schema.delete_class(collection)
                    logger.info(f"Deleted existing collection: {collection}")
            except Exception as e:
                logger.warning(f"Could not delete {collection}: {e}")
    
    def create_social_post_collection(self):
        """
        Create SocialPost collection for storing social media posts with embeddings
        
        Schema Design:
        - Vector dimension: 384 (from all-MiniLM-L6-v2 model)
        - Index type: HNSW (Hierarchical Navigable Small World)
        - Distance metric: cosine (best for normalized embeddings)
        """
        
        social_post_schema = {
            "class": "SocialPost",
            "description": "Social media posts with product analysis and embeddings",
            "vectorizer": "none",  # We provide pre-computed embeddings from Kafka
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "skip": False,
                "cleanupIntervalSeconds": 300,
                "maxConnections": 64,  # Higher = better recall, more memory
                "efConstruction": 128,  # Higher = better index quality, slower build
                "ef": -1,  # Dynamic at query time
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
                "dynamicEfFactor": 8,
                "vectorCacheMaxObjects": 1000000,
                "flatSearchCutoff": 40000,
                "distance": "cosine"  # cosine, dot, l2-squared, manhattan, hamming
            },
            "properties": [
                {
                    "name": "postId",
                    "dataType": ["text"],
                    "description": "Unique identifier for the post",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "platform",
                    "dataType": ["text"],
                    "description": "Social media platform (tiktok, facebook)",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Post content (anonymized)",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "authorHash",
                    "dataType": ["text"],
                    "description": "Hashed author identifier",
                    "indexInverted": True,
                    "indexSearchable": False
                },
                {
                    "name": "productCategory",
                    "dataType": ["text"],
                    "description": "Detected product category",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "categoryConfidence",
                    "dataType": ["number"],
                    "description": "Confidence score for category (0.0-1.0)"
                },
                {
                    "name": "engagementCount",
                    "dataType": ["int"],
                    "description": "Total engagement (likes + comments + shares)"
                },
                {
                    "name": "likesCount",
                    "dataType": ["int"],
                    "description": "Number of likes"
                },
                {
                    "name": "commentsCount",
                    "dataType": ["int"],
                    "description": "Number of comments"
                },
                {
                    "name": "sharesCount",
                    "dataType": ["int"],
                    "description": "Number of shares"
                },
                {
                    "name": "postedAt",
                    "dataType": ["date"],
                    "description": "When the post was published"
                },
                {
                    "name": "weatherCondition",
                    "dataType": ["text"],
                    "description": "Weather condition at post time",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "temperature",
                    "dataType": ["number"],
                    "description": "Temperature in Celsius"
                },
                {
                    "name": "humidity",
                    "dataType": ["number"],
                    "description": "Humidity percentage"
                },
                {
                    "name": "isWeekend",
                    "dataType": ["boolean"],
                    "description": "Whether posted on weekend"
                },
                {
                    "name": "hourOfDay",
                    "dataType": ["int"],
                    "description": "Hour when posted (0-23)"
                },
                {
                    "name": "embeddingModel",
                    "dataType": ["text"],
                    "description": "Model used for embedding generation",
                    "indexInverted": False,
                    "indexSearchable": False
                },
                {
                    "name": "anonymized",
                    "dataType": ["boolean"],
                    "description": "Whether PII was anonymized"
                },
                {
                    "name": "enriched",
                    "dataType": ["boolean"],
                    "description": "Whether context enrichment was applied"
                },
                {
                    "name": "ingestionTime",
                    "dataType": ["date"],
                    "description": "When ingested into Weaviate"
                }
            ]
        }
        
        try:
            self.client.schema.create_class(social_post_schema)
            logger.info("✓ Created SocialPost collection")
            return True
        except Exception as e:
            logger.error(f"Failed to create SocialPost collection: {e}")
            return False
    
    def create_market_order_collection(self):
        """
        Create MarketOrder collection for storing e-commerce orders with embeddings
        
        Schema Design:
        - Vector dimension: 384 (from all-MiniLM-L6-v2 model)
        - Index type: HNSW
        - Distance metric: cosine
        """
        
        market_order_schema = {
            "class": "MarketOrder",
            "description": "E-commerce orders with customer behavior embeddings",
            "vectorizer": "none",  # We provide pre-computed embeddings from Kafka
            "vectorIndexType": "hnsw",
            "vectorIndexConfig": {
                "skip": False,
                "cleanupIntervalSeconds": 300,
                "maxConnections": 64,
                "efConstruction": 128,
                "ef": -1,
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
                "dynamicEfFactor": 8,
                "vectorCacheMaxObjects": 1000000,
                "flatSearchCutoff": 40000,
                "distance": "cosine"
            },
            "properties": [
                {
                    "name": "orderId",
                    "dataType": ["text"],
                    "description": "Unique order identifier",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "platform",
                    "dataType": ["text"],
                    "description": "E-commerce platform (shopify, daraz)",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "customerIdHash",
                    "dataType": ["text"],
                    "description": "Hashed customer identifier",
                    "indexInverted": True,
                    "indexSearchable": False
                },
                {
                    "name": "productId",
                    "dataType": ["text"],
                    "description": "Product identifier",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "productName",
                    "dataType": ["text"],
                    "description": "Product name",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "productCategory",
                    "dataType": ["text"],
                    "description": "Detected product category",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "categoryConfidence",
                    "dataType": ["number"],
                    "description": "Category detection confidence (0.0-1.0)"
                },
                {
                    "name": "quantity",
                    "dataType": ["int"],
                    "description": "Order quantity"
                },
                {
                    "name": "unitPrice",
                    "dataType": ["number"],
                    "description": "Price per unit"
                },
                {
                    "name": "totalPrice",
                    "dataType": ["number"],
                    "description": "Total order value"
                },
                {
                    "name": "currency",
                    "dataType": ["text"],
                    "description": "Currency code (BDT, USD)"
                },
                {
                    "name": "status",
                    "dataType": ["text"],
                    "description": "Order status",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "paymentMethod",
                    "dataType": ["text"],
                    "description": "Payment method used",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "paymentStatus",
                    "dataType": ["text"],
                    "description": "Payment status",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "shippingRegion",
                    "dataType": ["text"],
                    "description": "Shipping region/division",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "shippingCity",
                    "dataType": ["text"],
                    "description": "Shipping city",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "createdAt",
                    "dataType": ["date"],
                    "description": "Order creation timestamp"
                },
                {
                    "name": "weatherCondition",
                    "dataType": ["text"],
                    "description": "Weather at order time",
                    "indexInverted": True,
                    "indexSearchable": True
                },
                {
                    "name": "temperature",
                    "dataType": ["number"],
                    "description": "Temperature in Celsius"
                },
                {
                    "name": "humidity",
                    "dataType": ["number"],
                    "description": "Humidity percentage"
                },
                {
                    "name": "isWeekend",
                    "dataType": ["boolean"],
                    "description": "Whether ordered on weekend"
                },
                {
                    "name": "hourOfDay",
                    "dataType": ["int"],
                    "description": "Hour when ordered (0-23)"
                },
                {
                    "name": "embeddingModel",
                    "dataType": ["text"],
                    "description": "Model used for embedding generation",
                    "indexInverted": False,
                    "indexSearchable": False
                },
                {
                    "name": "anonymized",
                    "dataType": ["boolean"],
                    "description": "Whether PII was anonymized"
                },
                {
                    "name": "enriched",
                    "dataType": ["boolean"],
                    "description": "Whether context enrichment was applied"
                },
                {
                    "name": "ingestionTime",
                    "dataType": ["date"],
                    "description": "When ingested into Weaviate"
                }
            ]
        }
        
        try:
            self.client.schema.create_class(market_order_schema)
            logger.info("✓ Created MarketOrder collection")
            return True
        except Exception as e:
            logger.error(f"Failed to create MarketOrder collection: {e}")
            return False
    
    def verify_schema(self):
        """Verify that collections were created successfully"""
        try:
            schema = self.client.schema.get()
            collections = [c['class'] for c in schema.get('classes', [])]
            
            logger.info("\n=== Weaviate Schema Verification ===")
            logger.info(f"Connected to: {self.weaviate_url}")
            logger.info(f"Collections found: {len(collections)}")
            
            for collection in ['SocialPost', 'MarketOrder']:
                if collection in collections:
                    # Get collection details
                    collection_schema = self.client.schema.get(collection)
                    props = len(collection_schema.get('properties', []))
                    vector_config = collection_schema.get('vectorIndexConfig', {})
                    
                    logger.info(f"\n✓ {collection}")
                    logger.info(f"  Properties: {props}")
                    logger.info(f"  Vector Index: {collection_schema.get('vectorIndexType', 'N/A')}")
                    logger.info(f"  Distance Metric: {vector_config.get('distance', 'N/A')}")
                    logger.info(f"  Max Connections: {vector_config.get('maxConnections', 'N/A')}")
                else:
                    logger.error(f"✗ {collection} not found")
            
            return True
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False
    
    def setup_schema(self, force_recreate: bool = False):
        """
        Main method to setup complete Weaviate schema
        
        Args:
            force_recreate: If True, delete existing collections and recreate
        """
        logger.info("Starting Weaviate schema setup...")
        
        if force_recreate:
            logger.warning("Force recreate enabled - deleting existing collections")
            self.delete_existing_collections()
        
        # Create collections
        success = []
        success.append(self.create_social_post_collection())
        success.append(self.create_market_order_collection())
        
        # Verify
        self.verify_schema()
        
        if all(success):
            logger.info("\n✓ Schema setup completed successfully!")
            return True
        else:
            logger.error("\n✗ Schema setup failed")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Weaviate schema for MillionX')
    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='Delete existing collections and recreate (WARNING: data loss)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing schema without creating'
    )
    
    args = parser.parse_args()
    
    try:
        manager = WeaviateSchemaManager()
        
        if args.verify_only:
            manager.verify_schema()
        else:
            manager.setup_schema(force_recreate=args.force_recreate)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
