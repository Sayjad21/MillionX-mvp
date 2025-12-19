"""
Weather Fetcher Service for MillionX Phase 2

Fetches current weather data for major Bangladesh cities and publishes to Kafka.
This service runs as a CronJob (hourly) to feed the Context Enricher processor.

Weather data includes:
- Temperature, humidity, pressure
- Weather condition (rain, clear, clouds)
- Wind speed and direction
- Visibility

Target cities: Dhaka, Chittagong, Sylhet, Khulna, Rajshahi, Barisal, Rangpur, Mymensingh

Author: MillionX Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherFetcher:
    """Fetches weather data and publishes to Kafka"""
    
    # Major cities in Bangladesh (8 divisions + capital)
    BANGLADESH_CITIES = [
        {'name': 'Dhaka', 'lat': 23.8103, 'lon': 90.4125},
        {'name': 'Chittagong', 'lat': 22.3569, 'lon': 91.7832},
        {'name': 'Sylhet', 'lat': 24.8949, 'lon': 91.8687},
        {'name': 'Khulna', 'lat': 22.8456, 'lon': 89.5403},
        {'name': 'Rajshahi', 'lat': 24.3745, 'lon': 88.6042},
        {'name': 'Barisal', 'lat': 22.7010, 'lon': 90.3535},
        {'name': 'Rangpur', 'lat': 25.7439, 'lon': 89.2752},
        {'name': 'Mymensingh', 'lat': 24.7471, 'lon': 90.4203}
    ]
    
    def __init__(self):
        """Initialize Weather Fetcher"""
        
        # OpenWeatherMap API configuration
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable not set")
        
        self.api_base_url = 'https://api.openweathermap.org/data/2.5/weather'
        
        # Kafka configuration
        self.kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.kafka_topic = os.getenv('KAFKA_WEATHER_TOPIC', 'context.weather')
        
        # Retry configuration
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY_SECONDS', '5'))
        
        # Initialize Kafka producer
        self._init_kafka_producer()
        
        # Statistics
        self.stats = {
            'total_fetched': 0,
            'total_published': 0,
            'total_errors': 0,
            'cities_processed': []
        }
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer with retry logic"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Preserve order
                compression_type='gzip'
            )
            logger.info(f"Connected to Kafka: {self.kafka_bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def fetch_weather(self, city: Dict[str, any]) -> Optional[Dict]:
        """
        Fetch weather data for a specific city
        
        Args:
            city: Dictionary with name, lat, lon
            
        Returns:
            Weather data dictionary or None if failed
        """
        city_name = city['name']
        
        params = {
            'lat': city['lat'],
            'lon': city['lon'],
            'appid': self.api_key,
            'units': 'metric'  # Celsius
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.api_base_url,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse and structure weather data
                    weather_data = {
                        'city': city_name,
                        'country': 'BD',
                        'latitude': city['lat'],
                        'longitude': city['lon'],
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'weather': {
                            'condition': data['weather'][0]['main'],
                            'description': data['weather'][0]['description'],
                            'icon': data['weather'][0]['icon']
                        },
                        'temperature': {
                            'current': data['main']['temp'],
                            'feels_like': data['main']['feels_like'],
                            'min': data['main']['temp_min'],
                            'max': data['main']['temp_max']
                        },
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'visibility': data.get('visibility', 0),
                        'wind': {
                            'speed': data['wind']['speed'],
                            'degree': data['wind'].get('deg', 0)
                        },
                        'clouds': data['clouds']['all'],
                        'sunrise': datetime.fromtimestamp(data['sys']['sunrise'], tz=timezone.utc).isoformat(),
                        'sunset': datetime.fromtimestamp(data['sys']['sunset'], tz=timezone.utc).isoformat()
                    }
                    
                    # Add rain/snow if present
                    if 'rain' in data:
                        weather_data['rain'] = data['rain']
                    if 'snow' in data:
                        weather_data['snow'] = data['snow']
                    
                    self.stats['total_fetched'] += 1
                    logger.info(f"✓ Fetched weather for {city_name}: {weather_data['weather']['condition']}, {weather_data['temperature']['current']}°C")
                    
                    return weather_data
                
                elif response.status_code == 401:
                    logger.error(f"API key authentication failed for {city_name}")
                    return None
                
                elif response.status_code == 429:
                    logger.warning(f"Rate limit exceeded for {city_name}, attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(self.retry_delay * (attempt + 1))
                
                else:
                    logger.warning(f"API request failed for {city_name}: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
            
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching weather for {city_name}, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Error fetching weather for {city_name}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        self.stats['total_errors'] += 1
        return None
    
    def publish_to_kafka(self, weather_data: Dict):
        """
        Publish weather data to Kafka topic
        
        Args:
            weather_data: Weather data dictionary
        """
        try:
            city = weather_data['city']
            
            # Use city name as message key for partitioning
            future = self.producer.send(
                self.kafka_topic,
                key=city,
                value=weather_data
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            self.stats['total_published'] += 1
            self.stats['cities_processed'].append(city)
            
            logger.info(
                f"✓ Published to Kafka: {self.kafka_topic} "
                f"partition={record_metadata.partition} offset={record_metadata.offset}"
            )
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing weather for {weather_data['city']}: {e}")
            self.stats['total_errors'] += 1
        except Exception as e:
            logger.error(f"Error publishing weather for {weather_data['city']}: {e}")
            self.stats['total_errors'] += 1
    
    def fetch_and_publish_all(self):
        """Fetch weather for all cities and publish to Kafka"""
        logger.info(f"Starting weather fetch for {len(self.BANGLADESH_CITIES)} cities...")
        
        start_time = time.time()
        
        for city in self.BANGLADESH_CITIES:
            weather_data = self.fetch_weather(city)
            
            if weather_data:
                self.publish_to_kafka(weather_data)
            
            # Rate limiting: 60 calls/minute on free tier
            time.sleep(1.1)  # ~55 requests/minute to stay safe
        
        # Flush remaining messages
        self.producer.flush()
        
        elapsed = time.time() - start_time
        
        # Print summary
        logger.info("\n=== Weather Fetch Summary ===")
        logger.info(f"Total cities: {len(self.BANGLADESH_CITIES)}")
        logger.info(f"Successfully fetched: {self.stats['total_fetched']}")
        logger.info(f"Published to Kafka: {self.stats['total_published']}")
        logger.info(f"Errors: {self.stats['total_errors']}")
        logger.info(f"Elapsed time: {elapsed:.2f}s")
        logger.info(f"Cities processed: {', '.join(self.stats['cities_processed'])}")
        
        return self.stats['total_errors'] == 0
    
    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


def main():
    """Main entry point for CronJob execution"""
    logger.info("Weather Fetcher Service starting...")
    
    try:
        fetcher = WeatherFetcher()
        success = fetcher.fetch_and_publish_all()
        fetcher.close()
        
        if success:
            logger.info("Weather fetch completed successfully")
            sys.exit(0)
        else:
            logger.error("Weather fetch completed with errors")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
