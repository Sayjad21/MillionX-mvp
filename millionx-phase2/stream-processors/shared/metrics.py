"""
Metrics collection for stream processors
Integrates with Prometheus for monitoring
"""

import time
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# In-memory metrics storage (will be exposed via Faust web interface)
metrics_store = {
    'messages_processed': {},
    'processing_latency': {},
    'errors': {},
    'dlq_sent': {},
}


def record_message_processed(processor_name: str, topic: str):
    """Record a successfully processed message"""
    key = f"{processor_name}.{topic}"
    metrics_store['messages_processed'][key] = metrics_store['messages_processed'].get(key, 0) + 1


def record_processing_latency(processor_name: str, latency_ms: float):
    """Record processing latency"""
    key = processor_name
    if key not in metrics_store['processing_latency']:
        metrics_store['processing_latency'][key] = []
    
    # Keep last 1000 samples for P95/P99 calculation
    latencies = metrics_store['processing_latency'][key]
    latencies.append(latency_ms)
    if len(latencies) > 1000:
        latencies.pop(0)


def record_error(processor_name: str, error_type: str):
    """Record an error"""
    key = f"{processor_name}.{error_type}"
    metrics_store['errors'][key] = metrics_store['errors'].get(key, 0) + 1


def record_dlq_sent(processor_name: str, dlq_topic: str):
    """Record a message sent to DLQ"""
    key = f"{processor_name}.{dlq_topic}"
    metrics_store['dlq_sent'][key] = metrics_store['dlq_sent'].get(key, 0) + 1


def measure_latency(processor_name: str):
    """
    Decorator to measure processing latency
    
    Usage:
        @measure_latency('privacy_shield')
        async def process_message(self, message):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                record_processing_latency(processor_name, latency_ms)
                return result
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                record_processing_latency(processor_name, latency_ms)
                record_error(processor_name, type(e).__name__)
                raise
        return wrapper
    return decorator


def get_metrics_summary():
    """Get current metrics summary"""
    summary = {
        'messages_processed': sum(metrics_store['messages_processed'].values()),
        'total_errors': sum(metrics_store['errors'].values()),
        'total_dlq_sent': sum(metrics_store['dlq_sent'].values()),
        'processors': {}
    }
    
    # Calculate P95 latency per processor
    for processor_name, latencies in metrics_store['processing_latency'].items():
        if latencies:
            sorted_latencies = sorted(latencies)
            p50_idx = int(len(sorted_latencies) * 0.50)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            
            summary['processors'][processor_name] = {
                'p50_latency_ms': sorted_latencies[p50_idx] if p50_idx < len(sorted_latencies) else 0,
                'p95_latency_ms': sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else 0,
                'p99_latency_ms': sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else 0,
                'avg_latency_ms': sum(latencies) / len(latencies),
                'sample_count': len(latencies)
            }
    
    return summary


def log_metrics_summary():
    """Log current metrics summary"""
    summary = get_metrics_summary()
    logger.info("📊 Metrics Summary:")
    logger.info(f"  Total Messages Processed: {summary['messages_processed']}")
    logger.info(f"  Total Errors: {summary['total_errors']}")
    logger.info(f"  Total DLQ Sent: {summary['total_dlq_sent']}")
    
    for processor, stats in summary['processors'].items():
        logger.info(f"  {processor}:")
        logger.info(f"    P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        logger.info(f"    P95 Latency: {stats['p95_latency_ms']:.2f}ms")
        logger.info(f"    P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        logger.info(f"    Avg Latency: {stats['avg_latency_ms']:.2f}ms")
