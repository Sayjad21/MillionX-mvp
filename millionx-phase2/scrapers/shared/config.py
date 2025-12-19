"""
Configuration Management for Scrapers
Centralized config with environment variable support
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Global configuration for all scrapers"""
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_COMPRESSION = os.getenv('KAFKA_COMPRESSION', 'gzip')
    
    # Proxy Configuration (comma-separated list)
    PROXY_LIST_STR = os.getenv('PROXY_LIST', '')
    PROXY_LIST: List[str] = [p.strip() for p in PROXY_LIST_STR.split(',') if p.strip()]
    
    # Scraping Behavior
    USE_PROXIES = len(PROXY_LIST) > 0
    MIN_DELAY_SECONDS = float(os.getenv('MIN_SCRAPE_DELAY', '3'))
    MAX_DELAY_SECONDS = float(os.getenv('MAX_SCRAPE_DELAY', '8'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    PAGE_TIMEOUT_MS = int(os.getenv('PAGE_TIMEOUT_MS', '30000'))
    
    # Apify Fallback (optional)
    USE_APIFY = os.getenv('USE_APIFY', 'false').lower() == 'true'
    APIFY_TOKEN = os.getenv('APIFY_TOKEN', '')
    
    # TikTok Specific
    TIKTOK_KEYWORDS = os.getenv(
        'TIKTOK_KEYWORDS',
        'smartphone,laptop,electronics,fashion,shoes,makeup,gadgets,trending products'
    ).split(',')
    TIKTOK_MAX_POSTS_PER_RUN = int(os.getenv('TIKTOK_MAX_POSTS', '50'))
    
    # Facebook Specific
    FACEBOOK_PAGE_IDS = os.getenv('FACEBOOK_PAGE_IDS', '').split(',')
    FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
    
    # Shopify Specific
    SHOPIFY_SHOP_URL = os.getenv('SHOPIFY_SHOP_URL', '')
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2024-01')
    
    # Daraz Specific
    DARAZ_APP_KEY = os.getenv('DARAZ_APP_KEY', '')
    DARAZ_APP_SECRET = os.getenv('DARAZ_APP_SECRET', '')
    DARAZ_API_URL = os.getenv('DARAZ_API_URL', 'https://api.daraz.com.bd/rest')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # User Agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.KAFKA_BOOTSTRAP_SERVERS:
            errors.append("KAFKA_BOOTSTRAP_SERVERS not set")
        
        if cls.USE_PROXIES and len(cls.PROXY_LIST) == 0:
            errors.append("USE_PROXIES is true but PROXY_LIST is empty")
        
        if cls.USE_APIFY and not cls.APIFY_TOKEN:
            errors.append("USE_APIFY is true but APIFY_TOKEN not set")
        
        # Warn about missing optional configs
        if not cls.FACEBOOK_ACCESS_TOKEN:
            errors.append("WARNING: FACEBOOK_ACCESS_TOKEN not set (Facebook scraper will not work)")
        
        if not cls.SHOPIFY_ACCESS_TOKEN:
            errors.append("WARNING: SHOPIFY_ACCESS_TOKEN not set (Shopify integration will not work)")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (masks sensitive values)"""
        print("=" * 60)
        print("MillionX Scraper Configuration")
        print("=" * 60)
        print(f"Kafka Bootstrap: {cls.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"Use Proxies: {cls.USE_PROXIES} ({len(cls.PROXY_LIST)} proxies loaded)")
        print(f"Use Apify Fallback: {cls.USE_APIFY}")
        print(f"Scrape Delay: {cls.MIN_DELAY_SECONDS}-{cls.MAX_DELAY_SECONDS}s")
        print(f"Max Retries: {cls.MAX_RETRIES}")
        print(f"TikTok Keywords: {', '.join(cls.TIKTOK_KEYWORDS[:5])}...")
        print(f"Facebook Token: {'✅ Set' if cls.FACEBOOK_ACCESS_TOKEN else '❌ Not Set'}")
        print(f"Shopify Token: {'✅ Set' if cls.SHOPIFY_ACCESS_TOKEN else '❌ Not Set'}")
        print(f"Daraz API Key: {'✅ Set' if cls.DARAZ_APP_KEY else '❌ Not Set'}")
        print("=" * 60)


# Usage
if __name__ == "__main__":
    Config.print_config()
    
    errors = Config.validate()
    if errors:
        print("\n⚠️  Configuration Issues:")
        for error in errors:
            print(f"  - {error}")
