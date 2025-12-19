"""
Dead Letter Queue (DLQ) Handler for MillionX Phase 2
Routes failed messages to appropriate DLQ topics with error metadata
"""
from kafka_producer import KafkaProducerClient
from datetime import datetime
import logging
import traceback
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DLQHandler:
    """
    Handles failed messages by routing them to Dead Letter Queue topics
    with error metadata for debugging and reprocessing
    """
    
    DLQ_TOPICS = {
        "social": "dead-letters-social",
        "market": "dead-letters-market",
        "validation": "schema-validation-errors"
    }
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """Initialize DLQ producers for all error topics"""
        self.dlq_producers = {}
        
        for category, topic in self.DLQ_TOPICS.items():
            try:
                self.dlq_producers[category] = KafkaProducerClient(
                    topic=topic,
                    bootstrap_servers=bootstrap_servers
                )
                logger.info(f"✅ DLQ producer initialized for: {topic}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize DLQ producer for {topic}: {e}")
    
    def send_to_dlq(
        self,
        category: str,
        original_data: Dict[str, Any],
        error: Exception,
        source_topic: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send failed message to appropriate DLQ
        
        Args:
            category: DLQ category ('social', 'market', 'validation')
            original_data: The data that failed processing
            error: The exception that was raised
            source_topic: Original Kafka topic the message was destined for
            additional_context: Optional dict with extra debugging info
            
        Returns:
            True if DLQ send successful, False otherwise
        """
        if category not in self.DLQ_TOPICS:
            logger.error(f"❌ Invalid DLQ category: {category}")
            return False
        
        try:
            # Build DLQ message with metadata
            dlq_message = {
                "original_data": original_data,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc()
                },
                "metadata": {
                    "source_topic": source_topic,
                    "dlq_category": category,
                    "dlq_timestamp": datetime.utcnow().isoformat(),
                    "additional_context": additional_context or {}
                }
            }
            
            # Send to DLQ
            producer = self.dlq_producers[category]
            success = producer.send_message(dlq_message)
            
            if success:
                logger.warning(
                    f"⚠️  Message sent to DLQ: {self.DLQ_TOPICS[category]} "
                    f"(Error: {type(error).__name__})"
                )
            else:
                logger.error(
                    f"❌ Failed to send message to DLQ: {self.DLQ_TOPICS[category]}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Critical error in DLQ handler: {e}")
            return False
    
    def close_all(self):
        """Close all DLQ producer connections"""
        for category, producer in self.dlq_producers.items():
            try:
                producer.close()
                logger.info(f"✅ Closed DLQ producer for: {category}")
            except Exception as e:
                logger.error(f"❌ Error closing DLQ producer for {category}: {e}")


# Convenience functions for quick usage
def send_to_social_dlq(
    data: Dict[str, Any],
    error: Exception,
    source_topic: str = "source.social.*",
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """Send social scraping failure to DLQ"""
    handler = DLQHandler()
    result = handler.send_to_dlq("social", data, error, source_topic, additional_context)
    handler.close_all()
    return result


def send_to_market_dlq(
    data: Dict[str, Any],
    error: Exception,
    source_topic: str = "source.market.*",
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """Send market API failure to DLQ"""
    handler = DLQHandler()
    result = handler.send_to_dlq("market", data, error, source_topic, additional_context)
    handler.close_all()
    return result


def send_to_validation_dlq(
    data: Dict[str, Any],
    error: Exception,
    source_topic: str,
    additional_context: Optional[Dict[str, Any]] = None
) -> bool:
    """Send schema validation failure to DLQ"""
    handler = DLQHandler()
    result = handler.send_to_dlq("validation", data, error, source_topic, additional_context)
    handler.close_all()
    return result


# Usage example
if __name__ == "__main__":
    # Test DLQ handler
    handler = DLQHandler()
    
    test_data = {
        "post_id": "invalid123",
        "content": "Test post with missing fields"
    }
    
    try:
        # Simulate validation error
        raise ValueError("Missing required field: author")
    except ValueError as e:
        handler.send_to_dlq(
            category="validation",
            original_data=test_data,
            error=e,
            source_topic="source.social.tiktok",
            additional_context={"scraper": "tiktok", "version": "1.0"}
        )
    
    handler.close_all()
