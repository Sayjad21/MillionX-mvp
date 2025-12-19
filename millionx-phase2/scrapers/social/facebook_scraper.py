"""
Facebook Graph API Client
Uses official Facebook Graph API for reliable data access
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
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


class FacebookScraper:
    """
    Facebook Graph API client for scraping public posts from pages
    More reliable than web scraping, but requires API access tokens
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, page_ids: List[str]):
        """
        Initialize Facebook scraper
        
        Args:
            page_ids: List of Facebook page IDs to scrape
        """
        self.page_ids = [pid.strip() for pid in page_ids if pid.strip()]
        self.access_token = Config.FACEBOOK_ACCESS_TOKEN
        self.producer = KafkaProducerClient("source.social.facebook")
        self.scraped_count = 0
        self.failed_count = 0
        
        if not self.access_token:
            raise ValueError("FACEBOOK_ACCESS_TOKEN not configured")
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to Facebook Graph API
        
        Args:
            endpoint: API endpoint (e.g., '/me/posts')
            params: Query parameters
            
        Returns:
            JSON response or None if failed
        """
        if params is None:
            params = {}
        
        params['access_token'] = self.access_token
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            return None
    
    def scrape_page_posts(
        self, 
        page_id: str, 
        limit: int = 25,
        since_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Scrape posts from a Facebook page
        
        Args:
            page_id: Facebook page ID
            limit: Maximum posts to fetch
            since_hours: Only fetch posts from last N hours
            
        Returns:
            List of post dictionaries
        """
        posts = []
        since_timestamp = int((datetime.utcnow() - timedelta(hours=since_hours)).timestamp())
        
        logger.info(f"🔍 Scraping Facebook page: {page_id}")
        
        # Request page posts with specific fields
        endpoint = f"/{page_id}/posts"
        params = {
            'fields': 'id,message,created_time,permalink_url,from,shares,reactions.summary(true),comments.summary(true)',
            'limit': limit,
            'since': since_timestamp
        }
        
        response = self._make_request(endpoint, params)
        
        if not response or 'data' not in response:
            logger.warning(f"⚠️  No data returned for page: {page_id}")
            return posts
        
        # Process posts
        for post in response['data']:
            try:
                post_data = self._transform_post(post, page_id)
                if post_data:
                    posts.append(post_data)
                    self.scraped_count += 1
            except Exception as e:
                logger.error(f"❌ Error transforming post {post.get('id')}: {e}")
                self.failed_count += 1
        
        logger.info(f"📊 Scraped {len(posts)} posts from page {page_id}")
        return posts
    
    def _transform_post(self, fb_post: Dict[str, Any], page_id: str) -> Optional[Dict[str, Any]]:
        """
        Transform Facebook Graph API response to our schema
        
        Args:
            fb_post: Raw Facebook post data
            page_id: Page ID for reference
            
        Returns:
            Transformed post dictionary
        """
        try:
            # Extract engagement metrics
            reactions_count = fb_post.get('reactions', {}).get('summary', {}).get('total_count', 0)
            comments_count = fb_post.get('comments', {}).get('summary', {}).get('total_count', 0)
            shares_count = fb_post.get('shares', {}).get('count', 0)
            
            # Extract hashtags from message
            message = fb_post.get('message', '')
            hashtags = [
                tag.strip('#').lower() 
                for word in message.split() 
                if word.startswith('#')
                for tag in [word]
            ]
            
            # Build post data
            post_data = {
                "post_id": f"facebook_{fb_post['id']}",
                "platform": "facebook",
                "content": message or "No caption",
                "author": fb_post.get('from', {}).get('name', f"Page {page_id}"),
                "author_id": fb_post.get('from', {}).get('id', page_id),
                "engagement_count": reactions_count + comments_count + shares_count,
                "likes_count": reactions_count,  # Reactions = likes + love + wow + etc
                "comments_count": comments_count,
                "shares_count": shares_count,
                "hashtags": hashtags,
                "mentioned_products": [],  # Could extract with NLP in stream processor
                "post_url": fb_post.get('permalink_url', f"https://facebook.com/{fb_post['id']}"),
                "posted_at": fb_post.get('created_time', datetime.utcnow().isoformat()),
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            return post_data
            
        except Exception as e:
            logger.error(f"❌ Error transforming post: {e}")
            return None
    
    def _send_to_kafka(self, post_data: Dict[str, Any]) -> bool:
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
                    source_topic="source.social.facebook",
                    additional_context={"scraper": "facebook", "validation": "pydantic"}
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
    
    def scrape_all_pages(self, posts_per_page: int = 25):
        """
        Scrape all configured Facebook pages
        
        Args:
            posts_per_page: Max posts to scrape per page
        """
        logger.info("🚀 Starting Facebook scraper")
        logger.info(f"📋 Pages to scrape: {len(self.page_ids)}")
        
        if not self.page_ids:
            logger.error("❌ No Facebook page IDs configured")
            return
        
        try:
            for page_id in self.page_ids:
                logger.info(f"\n{'='*60}")
                logger.info(f"Scraping page: {page_id}")
                logger.info('='*60)
                
                # Scrape posts
                posts = self.scrape_page_posts(page_id, limit=posts_per_page)
                
                # Send to Kafka
                for post in posts:
                    self._send_to_kafka(post)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Scraping complete!")
            logger.info(f"   Successfully scraped: {self.scraped_count}")
            logger.info(f"   Failed: {self.failed_count}")
            logger.info('='*60)
            
        except Exception as e:
            logger.error(f"❌ Critical error in Facebook scraper: {e}")
            raise
        finally:
            self.producer.close()


def main():
    """Entry point for Facebook scraper"""
    page_ids = Config.FACEBOOK_PAGE_IDS
    
    if not page_ids or not any(page_ids):
        logger.error("❌ No Facebook page IDs configured. Set FACEBOOK_PAGE_IDS environment variable")
        return
    
    scraper = FacebookScraper(page_ids)
    scraper.scrape_all_pages()


if __name__ == "__main__":
    main()
