"""
BeautifulSoup-based article extractor
Custom patterns for Korean news sites and fallback for others
"""
import asyncio
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
import json
from .base import BaseExtractor


class BS4Extractor(BaseExtractor):
    """
    BeautifulSoup extractor - Third fallback with Korean news site patterns
    Handles site-specific structures with multiple extraction strategies
    """
    
    name = "beautifulsoup"
    
    # Korean news site specific selectors
    SITE_PATTERNS = {
        # 네이버 뉴스
        "n.news.naver.com": {
            "title": ["h2#title_area", "h2.media_end_head_headline", ".article_header h3"],
            "content": ["article#dic_area", "#articleBodyContents", "#articeBody"],
            "author": [".media_end_head_journalist_name", ".byline", ".reporter"],
            "date": [".media_end_head_info_datestamp_time", "span.t11"],
            "category": [".media_end_categorize a", "em.media_end_head_top_channel_layer_item"],
        },
        # 다음 뉴스
        "v.daum.net": {
            "title": ["h3.tit_view", "h2.tit_newsview"],
            "content": ["div.article_view", "#harmonyContainer", "div#mArticle"],
            "author": ["span.info_view .txt_info", ".writer"],
            "date": ["span.num_date", "span.txt_info"],
            "category": ["span.txt_category", "a.link_cate"],
        },
        # 조선일보
        "www.chosun.com": {
            "title": ["h1.article-header__headline", "h1.news_title"],
            "content": ["section.article-body", "div.article-body__content", "#news_body_area"],
            "author": [".article-header__journalist-name", ".author_name"],
            "date": [".article-header__date", "span.date"],
            "category": [".article-header__category", "div.categ a"],
        },
        # 중앙일보
        "www.joongang.co.kr": {
            "title": ["h1.headline", "h1#article_title"],
            "content": ["div#article_body", "div.article_body"],
            "author": [".byline", ".article_writer"],
            "date": [".date", ".article_date"],
            "category": [".article_category", ".sub_category"],
        },
        # 한겨레
        "www.hani.co.kr": {
            "title": ["h4.title", "h1.article-title"],
            "content": ["div.article-text", "div.text"],
            "author": [".byline", ".reporter-name"],
            "date": [".date-time", ".article-date"],
            "category": [".section-name", ".article-category"],
        },
        # 동아일보
        "www.donga.com": {
            "title": ["h1.title", "h2.title"],
            "content": ["div.article_txt", "section.news_view"],
            "author": [".writer", ".reporter"],
            "date": [".date", ".article_date"],
            "category": [".location a", ".category"],
        },
        # KBS
        "news.kbs.co.kr": {
            "title": ["h4.headline-title", "h2.tit-news"],
            "content": ["div.detail-body", "#cont_newstext"],
            "author": [".byline", ".reporter"],
            "date": [".date", ".input-date"],
            "category": [".headline-category", ".cate"],
            "video": ["div.player-wrap video", "div.vod-player"],
        },
        # MBC
        "imnews.imbc.com": {
            "title": ["h2.art_title", "h1.title"],
            "content": ["div.news_txt", "div.article_body"],
            "author": [".reporter", ".byline"],
            "date": [".time", ".date"],
            "category": [".category", ".section"],
            "video": [".vod_area video", ".player video"],
        },
        # SBS
        "news.sbs.co.kr": {
            "title": ["h1.article_title", "h1.news_title"],
            "content": ["div.article_cont_area", "div.text_area"],
            "author": [".reporter", ".byline"],
            "date": [".date", ".article_date"],
            "category": [".category", ".section"],
            "video": [".vod_player video", ".video-container"],
        },
        # JTBC
        "news.jtbc.co.kr": {
            "title": ["h2.headline_title", "h1.art_title"],
            "content": ["div.article_content", "div.artical_body"],
            "author": [".reporter_area", ".byline"],
            "date": [".date_area", ".article_date"],
            "category": [".nav_area", ".category"],
            "video": [".vod_wrap video", ".player_wrap"],
        },
        # YTN
        "www.ytn.co.kr": {
            "title": ["h2.title", "h1.news_title"],
            "content": ["div.article", "div.news_content"],
            "author": [".reporter", ".byline"],
            "date": [".date", ".news_date"],
            "category": [".category", ".section"],
            "video": [".video_box video", ".player"],
        },
    }
    
    # Generic selectors for unknown sites
    GENERIC_SELECTORS = {
        "title": [
            "h1.article-title", "h1.entry-title", "h1.post-title", 
            "h1[itemprop='headline']", "article h1", "main h1", "h1.title",
            ".article-header h1", ".post-header h1", "h1"
        ],
        "content": [
            "article.content", "div.article-content", "div.entry-content",
            "div.post-content", "div[itemprop='articleBody']", "article",
            "main article", ".article-body", ".story-body", "div.content"
        ],
        "author": [
            "[rel='author']", ".author", ".byline", "[itemprop='author']",
            ".article-author", ".writer", ".reporter", "span.name"
        ],
        "date": [
            "time[datetime]", "[itemprop='datePublished']", ".date",
            ".publish-date", ".article-date", ".post-date", "time"
        ],
        "category": [
            "[itemprop='articleSection']", ".category", ".section",
            ".article-category", "nav.breadcrumb a"
        ],
    }
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Extract article using BeautifulSoup with site-specific patterns"""
        try:
            html = await self._fetch_html(url, timeout)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            domain = self.get_domain(url)
            
            # Get site-specific or generic patterns
            patterns = self.SITE_PATTERNS.get(domain, self.GENERIC_SELECTORS)
            
            # Extract data
            title = self._extract_field(soup, patterns.get("title", self.GENERIC_SELECTORS["title"]))
            content = self._extract_content(soup, patterns.get("content", self.GENERIC_SELECTORS["content"]))
            author = self._extract_field(soup, patterns.get("author", self.GENERIC_SELECTORS["author"]))
            date = self._extract_date(soup, patterns.get("date", self.GENERIC_SELECTORS["date"]))
            category = self._extract_field(soup, patterns.get("category", self.GENERIC_SELECTORS["category"]))
            
            # Extract metadata
            meta = self._extract_meta(soup)
            
            # Extract media
            images = self._extract_images(soup, url)
            videos = self._extract_videos(soup, url, patterns.get("video", []))
            
            # Extract stats
            stats = self._extract_stats(soup)
            
            return {
                "url": url,
                "title": self.clean_text(title) or meta.get("og:title"),
                "content": self.clean_text(content),
                "summary": meta.get("description") or meta.get("og:description"),
                "published_date": self.parse_date(date) or meta.get("article:published_time"),
                "modified_date": meta.get("article:modified_time"),
                "author": self.clean_text(author) or meta.get("article:author"),
                "authors": self._parse_authors(author),
                "main_image_url": meta.get("og:image"),
                "image_urls": images,
                "video_url": videos[0] if videos else None,
                "video_urls": videos,
                "category": self.clean_text(category) or meta.get("article:section"),
                "tags": meta.get("keywords"),
                "keywords": meta.get("news_keywords"),
                "view_count": stats.get("view_count"),
                "like_count": stats.get("like_count"),
                "comment_count": stats.get("comment_count"),
                "source_name": meta.get("og:site_name"),
                "source_domain": domain,
                "language": meta.get("language"),
                "og_title": meta.get("og:title"),
                "og_description": meta.get("og:description"),
                "og_image": meta.get("og:image"),
                "og_type": meta.get("og:type"),
                "extraction_method": self.name
            }
            
        except Exception as e:
            print(f"BeautifulSoup extraction failed: {e}")
            return None
    
    async def _fetch_html(self, url: str, timeout: int) -> Optional[str]:
        """Fetch HTML content"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Failed to fetch URL: {e}")
            return None
    
    def _extract_field(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors and return first match"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except:
                continue
        return None
    
    def _extract_content(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract article content with better handling"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Remove unwanted elements
                    for tag in element.find_all(['script', 'style', 'aside', 'nav', 'footer', 'iframe']):
                        tag.decompose()
                    
                    # Get text with paragraph separation
                    paragraphs = element.find_all(['p', 'div'])
                    if paragraphs:
                        text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    else:
                        text = element.get_text(separator='\n', strip=True)
                    
                    if len(text) > 100:  # Minimum content length
                        return text
            except:
                continue
        return None
    
    def _extract_date(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract and parse date"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Check for datetime attribute
                    datetime_attr = element.get('datetime') or element.get('content')
                    if datetime_attr:
                        return datetime_attr
                    return element.get_text(strip=True)
            except:
                continue
        return None
    
    def _extract_meta(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from meta tags"""
        meta = {}
        
        # Open Graph
        for og in soup.find_all('meta', property=re.compile(r'^og:')):
            key = og.get('property')
            meta[key] = og.get('content')
        
        # Article metadata
        for article in soup.find_all('meta', property=re.compile(r'^article:')):
            key = article.get('property')
            meta[key] = article.get('content')
        
        # Standard meta tags
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            meta['description'] = description.get('content')
        
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            meta['keywords'] = [k.strip() for k in keywords.get('content', '').split(',')]
        
        news_keywords = soup.find('meta', attrs={'name': 'news_keywords'})
        if news_keywords:
            meta['news_keywords'] = [k.strip() for k in news_keywords.get('content', '').split(',')]
        
        # Language
        html_tag = soup.find('html')
        if html_tag:
            meta['language'] = html_tag.get('lang')
        
        return meta
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> Optional[List[str]]:
        """Extract images from article"""
        images = []
        
        # Find images in article area
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                normalized = self.normalize_url(src, base_url)
                if normalized and normalized not in images:
                    # Filter out icons and logos
                    if not any(x in normalized.lower() for x in ['icon', 'logo', 'pixel', 'tracker', 'btn', 'banner', 'ad_']):
                        images.append(normalized)
        
        return images[:10] if images else None
    
    def _extract_videos(self, soup: BeautifulSoup, base_url: str, extra_selectors: List[str] = None) -> Optional[List[str]]:
        """Extract video URLs"""
        videos = []
        
        # Try site-specific selectors first
        if extra_selectors:
            for selector in extra_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    src = elem.get('src') or elem.get('data-src')
                    if src:
                        videos.append(self.normalize_url(src, base_url))
        
        # Standard video elements
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                videos.append(self.normalize_url(src, base_url))
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    videos.append(self.normalize_url(src, base_url))
        
        # Iframes (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src') or iframe.get('data-src')
            if src and any(x in src.lower() for x in ['youtube', 'vimeo', 'dailymotion', 'video', 'player']):
                videos.append(src)
        
        # JSON-LD structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    video_obj = data.get('video') or data.get('videoObject')
                    if video_obj:
                        content_url = video_obj.get('contentUrl') or video_obj.get('embedUrl')
                        if content_url:
                            videos.append(content_url)
            except:
                pass
        
        videos = [v for v in videos if v]
        return list(dict.fromkeys(videos)) if videos else None
    
    def _extract_stats(self, soup: BeautifulSoup) -> Dict[str, Optional[int]]:
        """Extract view count, likes, comments"""
        stats = {
            "view_count": None,
            "like_count": None,
            "comment_count": None,
        }
        
        # Common patterns for stats
        view_patterns = ['.view-count', '.hit', '.views', '.read-count', '[class*="view"]', '[class*="hit"]']
        like_patterns = ['.like-count', '.likes', '.recommend', '[class*="like"]', '[class*="recommend"]']
        comment_patterns = ['.comment-count', '.comments', '.reply-count', '[class*="comment"]', '[class*="reply"]']
        
        for selector in view_patterns:
            elem = soup.select_one(selector)
            if elem:
                stats["view_count"] = self.extract_numbers(elem.get_text())
                break
        
        for selector in like_patterns:
            elem = soup.select_one(selector)
            if elem:
                stats["like_count"] = self.extract_numbers(elem.get_text())
                break
        
        for selector in comment_patterns:
            elem = soup.select_one(selector)
            if elem:
                stats["comment_count"] = self.extract_numbers(elem.get_text())
                break
        
        return stats
    
    def _parse_authors(self, author_str: Optional[str]) -> Optional[List[str]]:
        """Parse author string into list"""
        if not author_str:
            return None
        
        authors = re.split(r'[,;·/]|\s+and\s+|\s+&\s+|기자', author_str)
        authors = [self.clean_text(a) for a in authors if a and self.clean_text(a)]
        
        return authors if authors else None
