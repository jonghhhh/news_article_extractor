"""
Trafilatura-based article extractor
Fast and accurate for most news sites
"""
import asyncio
from typing import Optional, Dict, Any, List
import trafilatura
from trafilatura.settings import use_config
from trafilatura.metadata import extract_metadata
import httpx
import json
import re
from .base import BaseExtractor


class TrafilaturaExtractor(BaseExtractor):
    """
    Trafilatura extractor - First choice for speed and accuracy
    Handles most news sites well with built-in fallbacks
    """
    
    name = "trafilatura"
    
    def __init__(self):
        # Configure trafilatura for better extraction
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "100")
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Extract article using trafilatura"""
        try:
            # Fetch HTML content
            html = await self._fetch_html(url, timeout)
            if not html:
                return None
            
            # Extract main content
            result = trafilatura.extract(
                html,
                url=url,
                output_format='json',
                include_comments=False,
                include_tables=True,
                include_images=True,
                include_links=True,
                with_metadata=True,
                favor_precision=True,
                config=self.config
            )
            
            if not result:
                return None
            
            # Parse JSON result
            data = json.loads(result)
            
            # Extract additional metadata
            metadata = extract_metadata(html, url)
            
            # Extract images and videos from HTML
            images = self._extract_images(html, url)
            videos = self._extract_videos(html, url)
            
            # Build response
            return {
                "url": url,
                "title": self.clean_text(data.get("title")),
                "content": self.clean_text(data.get("text")),
                "summary": self.clean_text(data.get("description") or (metadata.description if metadata else None)),
                "published_date": self.parse_date(data.get("date")),
                "author": self.clean_text(data.get("author")),
                "authors": self._parse_authors(data.get("author")),
                "main_image_url": data.get("image") or (metadata.image if metadata else None),
                "image_urls": images,
                "video_url": videos[0] if videos else None,
                "video_urls": videos if videos else None,
                "category": self.clean_text(data.get("categories")),
                "tags": data.get("tags", "").split(",") if data.get("tags") else None,
                "keywords": metadata.keywords if metadata else None,
                "source_name": data.get("sitename") or (metadata.sitename if metadata else None),
                "source_domain": self.get_domain(url),
                "language": data.get("language"),
                "og_title": metadata.title if metadata else None,
                "og_description": metadata.description if metadata else None,
                "og_image": metadata.image if metadata else None,
                "extraction_method": self.name
            }
            
        except Exception as e:
            print(f"Trafilatura extraction failed: {e}")
            return None
    
    async def _fetch_html(self, url: str, timeout: int) -> Optional[str]:
        """Fetch HTML content with httpx"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Failed to fetch URL: {e}")
            return None
    
    def _parse_authors(self, author_str: Optional[str]) -> Optional[List[str]]:
        """Parse author string into list"""
        if not author_str:
            return None
        
        # Split by common separators
        authors = re.split(r'[,;·/]|\s+and\s+|\s+&\s+', author_str)
        authors = [self.clean_text(a) for a in authors if a and self.clean_text(a)]
        
        return authors if authors else None
    
    def _extract_images(self, html: str, base_url: str) -> Optional[List[str]]:
        """Extract image URLs from HTML"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            images = []
            
            # Find images in article content
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    normalized = self.normalize_url(src, base_url)
                    if normalized and normalized not in images:
                        # Filter out small icons and tracking pixels
                        if not any(x in normalized.lower() for x in ['icon', 'logo', 'pixel', 'tracker', 'avatar', 'btn', 'button']):
                            images.append(normalized)
            
            return images[:10] if images else None  # Limit to 10 images
        except:
            return None
    
    def _extract_videos(self, html: str, base_url: str) -> Optional[List[str]]:
        """Extract video URLs from HTML"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            videos = []
            
            # Find video elements
            for video in soup.find_all('video'):
                src = video.get('src')
                if src:
                    videos.append(self.normalize_url(src, base_url))
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src:
                        videos.append(self.normalize_url(src, base_url))
            
            # Find iframe embeds (YouTube, Vimeo, etc.)
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src') or iframe.get('data-src')
                if src and any(x in src.lower() for x in ['youtube', 'vimeo', 'dailymotion', 'video', 'player']):
                    videos.append(src)
            
            # Find og:video meta tag
            og_video = soup.find('meta', property='og:video')
            if og_video and og_video.get('content'):
                videos.append(og_video['content'])
            
            # Korean broadcast specific patterns
            for script in soup.find_all('script'):
                script_text = script.string or ''
                # KBS, MBC, SBS video patterns
                video_patterns = [
                    r'videoUrl["\s:]+["\']([^"\']+)["\']',
                    r'hlsUrl["\s:]+["\']([^"\']+)["\']',
                    r'mp4Url["\s:]+["\']([^"\']+)["\']',
                    r'vodUrl["\s:]+["\']([^"\']+)["\']',
                ]
                for pattern in video_patterns:
                    matches = re.findall(pattern, script_text)
                    videos.extend(matches)
            
            # Remove duplicates and None values
            videos = [v for v in videos if v]
            videos = list(dict.fromkeys(videos))
            
            return videos if videos else None
        except:
            return None
