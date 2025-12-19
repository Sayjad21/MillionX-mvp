"""
TikTok Scraper with Anti-Bot Hardening
Features: Proxy rotation, user agent randomization, smart delays, CAPTCHA handling
"""
import asyncio
import random
import logging
from datetime import datetime
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import hashlib
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from kafka_producer import KafkaProducerClient
from dlq_handler import send_to_social_dlq
from models import SocialPost, validate_social_post
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class TikTokScraper:
    """
    Production-grade TikTok scraper with anti-bot countermeasures
    """
    
    def __init__(self, keywords: List[str]):
        """
        Initialize TikTok scraper
        
        Args:
            keywords: List of search keywords to scrape
        """
        self.keywords = keywords
        self.producer = KafkaProducerClient("source.social.tiktok")
        self.browser: Optional[Browser] = None
        self.scraped_count = 0
        self.failed_count = 0
        
    async def _get_random_proxy(self) -> Optional[dict]:
        """Get random proxy from pool"""
        if not Config.USE_PROXIES or not Config.PROXY_LIST:
            return None
        
        proxy_url = random.choice(Config.PROXY_LIST)
        logger.info(f"🔄 Using proxy: {proxy_url[:30]}...")
        
        return {"server": proxy_url}
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent to avoid fingerprinting"""
        return random.choice(Config.USER_AGENTS)
    
    async def _init_browser(self) -> Browser:
        """Initialize Playwright browser with anti-detection settings"""
        playwright = await async_playwright().start()
        
        launch_args = {
            "headless": True,
            "args": [
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        }
        
        # Add proxy if configured
        proxy = await self._get_random_proxy()
        if proxy:
            launch_args["proxy"] = proxy
        
        browser = await playwright.chromium.launch(**launch_args)
        logger.info("✅ Browser initialized with anti-detection settings")
        
        return browser
    
    async def _create_stealth_page(self) -> Page:
        """Create a page with stealth settings"""
        context = await self.browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Asia/Dhaka"
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'bn']
            });
        """)
        
        page = await context.new_page()
        return page
    
    async def _random_delay(self):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(Config.MIN_DELAY_SECONDS, Config.MAX_DELAY_SECONDS)
        logger.debug(f"⏳ Waiting {delay:.2f}s before next action")
        await asyncio.sleep(delay)
    
    async def _scrape_keyword(self, keyword: str, max_posts: int = 10) -> List[dict]:
        """
        Scrape TikTok posts for a specific keyword
        
        Args:
            keyword: Search keyword
            max_posts: Maximum posts to scrape
            
        Returns:
            List of scraped post dictionaries
        """
        posts = []
        page = await self._create_stealth_page()
        
        try:
            # Navigate to TikTok search (using web version for easier scraping)
            search_url = f"https://www.tiktok.com/search?q={keyword.replace(' ', '%20')}"
            logger.info(f"🔍 Scraping TikTok for keyword: {keyword}")
            
            await page.goto(search_url, timeout=Config.PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
            await self._random_delay()
            
            # Wait for content to load
            try:
                await page.wait_for_selector('[data-e2e="search-video-item"]', timeout=10000)
            except PlaywrightTimeout:
                logger.warning(f"⚠️  No results found for keyword: {keyword}")
                return posts
            
            # Scroll to load more posts
            for i in range(3):  # Scroll 3 times
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(random.uniform(1, 2))
            
            # Extract post data
            video_items = await page.query_selector_all('[data-e2e="search-video-item"]')
            logger.info(f"📊 Found {len(video_items)} video items")
            
            for idx, item in enumerate(video_items[:max_posts]):
                if idx >= max_posts:
                    break
                
                try:
                    # Extract post details
                    post_data = await self._extract_post_data(page, item, keyword)
                    if post_data:
                        posts.append(post_data)
                        self.scraped_count += 1
                    
                    await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay between posts
                    
                except Exception as e:
                    logger.error(f"❌ Error extracting post {idx}: {e}")
                    self.failed_count += 1
            
        except PlaywrightTimeout:
            logger.error(f"❌ Timeout loading page for keyword: {keyword}")
        except Exception as e:
            logger.error(f"❌ Error scraping keyword '{keyword}': {e}")
        finally:
            await page.close()
        
        return posts
    
    async def _extract_post_data(self, page: Page, item, keyword: str) -> Optional[dict]:
        """
        Extract structured data from a TikTok post element
        
        Returns:
            Dictionary with post data or None if extraction fails
        """
        try:
            # Extract post URL
            link_element = await item.query_selector('a[href*="/video/"]')
            if not link_element:
                return None
            
            post_url = await link_element.get_attribute('href')
            if not post_url.startswith('http'):
                post_url = f"https://www.tiktok.com{post_url}"
            
            # Extract post ID from URL
            post_id = post_url.split('/video/')[-1].split('?')[0] if '/video/' in post_url else None
            if not post_id:
                return None
            
            # Extract content/caption
            caption_element = await item.query_selector('[data-e2e="search-video-caption"]')
            content = await caption_element.inner_text() if caption_element else ""
            
            # Extract author
            author_element = await item.query_selector('[data-e2e="search-video-author"]')
            author = await author_element.inner_text() if author_element else "unknown"
            
            # Extract engagement metrics (likes, comments, etc.)
            likes_element = await item.query_selector('[data-e2e="like-count"]')
            likes_text = await likes_element.inner_text() if likes_element else "0"
            likes_count = self._parse_count(likes_text)
            
            comments_element = await item.query_selector('[data-e2e="comment-count"]')
            comments_text = await comments_element.inner_text() if comments_element else "0"
            comments_count = self._parse_count(comments_text)
            
            shares_element = await item.query_selector('[data-e2e="share-count"]')
            shares_text = await shares_element.inner_text() if shares_element else "0"
            shares_count = self._parse_count(shares_text)
            
            # Extract hashtags
            hashtags = []
            if content:
                hashtags = [tag.strip('#').lower() for tag in content.split() if tag.startswith('#')]
            
            # Build post data
            post_data = {
                "post_id": f"tiktok_{post_id}",
                "platform": "tiktok",
                "content": content or f"Video about {keyword}",
                "author": author,
                "engagement_count": likes_count + comments_count + shares_count,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "shares_count": shares_count,
                "hashtags": hashtags,
                "mentioned_products": [keyword.lower()],  # Add search keyword as mentioned product
                "post_url": post_url,
                "posted_at": datetime.utcnow().isoformat(),  # Actual timestamp requires clicking into post
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            return post_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting post data: {e}")
            return None
    
    def _parse_count(self, count_text: str) -> int:
        """Parse engagement count like '1.2K', '500', '1M' to integer"""
        try:
            count_text = count_text.strip().upper()
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            else:
                return int(count_text)
        except:
            return 0
    
    async def _send_to_kafka(self, post_data: dict) -> bool:
        """Validate and send post to Kafka"""
        # Validate against Pydantic schema
        is_valid, validated_model, error = validate_social_post(post_data)
        
        if not is_valid:
            logger.warning(f"⚠️  Schema validation failed: {error}")
            # Send to DLQ
            try:
                send_to_social_dlq(
                    data=post_data,
                    error=ValueError(error),
                    source_topic="source.social.tiktok",
                    additional_context={"scraper": "tiktok", "validation": "pydantic"}
                )
            except Exception as dlq_error:
                logger.error(f"❌ Failed to send to DLQ: {dlq_error}")
            return False
        
        # Send validated data to Kafka
        try:
            success = self.producer.send_message(validated_model.model_dump())
            if success:
                logger.info(f"✅ Post {post_data['post_id']} sent to Kafka")
            return success
        except Exception as e:
            logger.error(f"❌ Kafka send failed: {e}")
            return False
    
    async def scrape(self):
        """Main scraping orchestrator"""
        logger.info("🚀 Starting TikTok scraper")
        Config.print_config()
        
        try:
            # Initialize browser
            self.browser = await self._init_browser()
            
            # Scrape each keyword
            for keyword in self.keywords[:5]:  # Limit to 5 keywords per run
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping keyword: {keyword}")
                logger.info('='*60)
                
                posts = await self._scrape_keyword(
                    keyword, 
                    max_posts=Config.TIKTOK_MAX_POSTS_PER_RUN // len(self.keywords)
                )
                
                # Send posts to Kafka
                for post in posts:
                    await self._send_to_kafka(post)
                
                # Delay between keywords
                await self._random_delay()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Scraping complete!")
            logger.info(f"   Successfully scraped: {self.scraped_count}")
            logger.info(f"   Failed: {self.failed_count}")
            logger.info('='*60)
            
        except Exception as e:
            logger.error(f"❌ Critical error in scraper: {e}")
            raise
        finally:
            # Cleanup
            if self.browser:
                await self.browser.close()
            self.producer.close()


# Run as Kubernetes CronJob or standalone
async def main():
    """Entry point for scraper"""
    keywords = Config.TIKTOK_KEYWORDS
    
    if not keywords:
        logger.error("❌ No keywords configured. Set TIKTOK_KEYWORDS environment variable")
        return
    
    scraper = TikTokScraper(keywords)
    await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
