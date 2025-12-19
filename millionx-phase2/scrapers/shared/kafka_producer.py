"""
Kafka Producer Client for MillionX Phase 2
Handles message production with retry logic and error handling
"""
from kafka import KafkaProducer
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """
    Wrapper around KafkaProducer with automatic serialization,
    error handling, and retry logic.
    """
    
    def __init__(
        self, 
        topic: str, 
        bootstrap_servers: str = "localhost:9092",
        compression_type: str = "gzip"
    ):
        """
        Initialize Kafka producer
        
        Args:
            topic: Target Kafka topic
            bootstrap_servers: Kafka broker addresses (comma-separated)
            compression_type: Message compression ('gzip', 'snappy', 'lz4', or None)
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type=compression_type,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,  # Retry failed sends
                max_in_flight_requests_per_connection=5,
                request_timeout_ms=30000,
                linger_ms=100,  # Batch messages for efficiency
                batch_size=16384  # 16KB batches
            )
            logger.info(f"✅ Kafka producer initialized for topic: {topic}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka producer: {e}")
            raise
    
    def send_message(
        self, 
        data: Dict[str, Any], 
        key: Optional[str] = None
    ) -> bool:
        """
        Send message to Kafka topic with automatic retry
        
        Args:
            data: Message payload (will be JSON serialized)
            key: Optional partition key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add metadata
            enriched_data = {
                **data,
                "kafka_ingestion_time": datetime.utcnow().isoformat(),
                "kafka_topic": self.topic
            }
            
            # Send message
            future = self.producer.send(
                self.topic,
                value=enriched_data,
                key=key.encode('utf-8') if key else None
            )
            
            # Wait for acknowledgment (blocking)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"✅ Message sent to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to {self.topic}: {e}")
            return False
    
    def send_batch(self, messages: list[Dict[str, Any]]) -> tuple[int, int]:
        """
        Send multiple messages in batch
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        success_count = 0
        failed_count = 0
        
        for msg in messages:
            if self.send_message(msg):
                success_count += 1
            else:
                failed_count += 1
        
        # Flush remaining buffered messages
        self.producer.flush()
        
        logger.info(
            f"📊 Batch send complete: {success_count} succeeded, "
            f"{failed_count} failed"
        )
        return success_count, failed_count
    
    def close(self):
        """Flush and close producer connection"""
        try:
            self.producer.flush()
            self.producer.close()
            logger.info(f"✅ Kafka producer closed for topic: {self.topic}")
        except Exception as e:
            logger.error(f"❌ Error closing Kafka producer: {e}")


# Usage example
if __name__ == "__main__":
    # Test producer
    producer = KafkaProducerClient("source.social.tiktok")
    
    test_message = {
        "post_id": "test123",
        "content": "This is a test post",
        "author": "test_user",
        "engagement_count": 100
    }
    
    producer.send_message(test_message)
    producer.close()
