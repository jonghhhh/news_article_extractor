"""
Newspaper3k-based article extractor
Good for mainstream news sites with standard article structure
"""
import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import newspaper
from newspaper import Article, Config
from .base import BaseExtractor


class NewspaperExtractor(BaseExtractor):
    """
    Newspaper3k extractor - Second fallback option
    Works well for standard news article formats
    """
    
    name = "newspaper3k"
    
    def __init__(self):
        self.config = Config()
        self.config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.config.request_timeout = 30
        self.config.fetch_images = True
        self.config.memoize_articles = False
        self.config.language = 'ko'  # Korean
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Extract article using newspaper3k"""
        try:
            self.config.request_timeout = timeout
            
            # Run newspaper in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._extract_sync, 
                    url
                )
            
            return result
            
        except Exception as e:
            print(f"Newspaper3k extraction failed: {e}")
            return None
    
    def _extract_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """Synchronous extraction logic"""
        try:
            article = Article(url, config=self.config)
            article.download()
            article.parse()
            
            # Try NLP for keywords (may fail for non-English)
            try:
                article.nlp()
                keywords = article.keywords
                summary = article.summary
            except:
                keywords = None
                summary = None
            
            # Extract images
            images = list(article.images) if article.images else None
            
            # Get authors
            authors = article.authors if article.authors else None
            
            # Get movies/videos
            videos = list(article.movies) if article.movies else None
            
            return {
                "url": url,
                "title": self.clean_text(article.title),
                "content": self.clean_text(article.text),
                "summary": self.clean_text(summary) or self.clean_text(article.meta_description),
                "published_date": self.parse_date(str(article.publish_date)) if article.publish_date else None,
                "author": authors[0] if authors else None,
                "authors": authors,
                "main_image_url": article.top_image,
                "image_urls": images[:10] if images else None,
                "video_url": videos[0] if videos else None,
                "video_urls": videos,
                "category": self.clean_text(article.meta_data.get('section')),
                "tags": list(article.tags) if article.tags else None,
                "keywords": keywords,
                "source_name": article.meta_data.get('og', {}).get('site_name') or article.source_url,
                "source_domain": self.get_domain(url),
                "language": article.meta_lang,
                "og_title": article.meta_data.get('og', {}).get('title'),
                "og_description": article.meta_data.get('og', {}).get('description'),
                "og_image": article.meta_data.get('og', {}).get('image'),
                "og_type": article.meta_data.get('og', {}).get('type'),
                "extraction_method": self.name
            }
            
        except Exception as e:
            print(f"Newspaper3k sync extraction failed: {e}")
            return None
