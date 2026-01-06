"""
News Article Extractors Package
Provides multiple extraction strategies with automatic fallback
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from .base import BaseExtractor
from .trafilatura_extractor import TrafilaturaExtractor
from .newspaper_extractor import NewspaperExtractor
from .bs4_extractor import BS4Extractor
from .playwright_extractor import PlaywrightExtractor


class ArticleExtractor:
    """
    Main article extraction engine with automatic fallback mechanism
    
    Extraction order (fastest to most comprehensive):
    1. Trafilatura - Fast, accurate for most sites
    2. Newspaper3k - Good for standard news formats
    3. BeautifulSoup - Custom patterns for Korean sites
    4. Playwright - Full JS rendering for dynamic sites
    """
    
    def __init__(self, use_playwright: bool = True):
        """
        Initialize extractor with available methods

        Args:
            use_playwright: Whether to include Playwright in fallback chain (default: True)
        """
        # Order: Trafilatura (fastest) -> Newspaper -> BS4 -> Playwright (most reliable)
        self.extractors: List[BaseExtractor] = [
            TrafilaturaExtractor(),
            NewspaperExtractor(),
            BS4Extractor(),
        ]

        if use_playwright:
            self.extractors.append(PlaywrightExtractor())
    
    async def extract(
        self, 
        url: str, 
        timeout: int = 30,
        methods_to_try: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract article data using fallback mechanism
        
        Args:
            url: Article URL
            timeout: Request timeout in seconds
            methods_to_try: Specific methods to try (optional)
            
        Returns:
            Dictionary with extraction result
        """
        methods_tried = []
        last_error = None
        
        # Filter extractors if specific methods requested
        extractors = self.extractors
        if methods_to_try:
            extractors = [e for e in self.extractors if e.name in methods_to_try]
        
        for extractor in extractors:
            methods_tried.append(extractor.name)
            
            try:
                result = await extractor.extract(url, timeout)
                
                if result and self._is_valid_extraction(result):
                    # Add extraction metadata
                    result["extraction_time"] = datetime.now().isoformat()
                    
                    return {
                        "success": True,
                        "data": result,
                        "methods_tried": methods_tried,
                        "error": None
                    }
                    
            except Exception as e:
                last_error = str(e)
                print(f"Extractor {extractor.name} failed: {e}")
                continue
        
        # All methods failed
        return {
            "success": False,
            "data": None,
            "methods_tried": methods_tried,
            "error": last_error or "All extraction methods failed"
        }
    
    def _is_valid_extraction(self, data: Dict[str, Any]) -> bool:
        """
        Check if extraction result is valid

        Validation criteria:
        - Must have both title AND content
        - Content must be at least 200 characters
        - Content should not be generic error messages or navigation text
        """
        has_title = bool(data.get("title")) and len(data.get("title", "").strip()) > 0
        content = data.get("content", "").strip()

        # Check content length
        has_content = bool(content) and len(content) > 200

        # Check for invalid content patterns (common on failed extractions)
        invalid_patterns = [
            "기사 섹션 분류 안내",
            "언론사의 분류를 따르고 있습니다",
            "페이지를 찾을 수 없습니다",
            "404",
            "not found",
            "접근이 거부되었습니다",
        ]

        # If content contains only invalid patterns, mark as invalid
        if has_content:
            content_lower = content.lower()
            if any(pattern.lower() in content_lower for pattern in invalid_patterns):
                # Check if content is ONLY these patterns (short content)
                if len(content) < 500:
                    return False

        return has_title and has_content
    
    async def extract_multiple(
        self, 
        urls: List[str], 
        timeout: int = 30,
        concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract multiple articles concurrently
        
        Args:
            urls: List of article URLs
            timeout: Request timeout per URL
            concurrency: Maximum concurrent extractions
            
        Returns:
            List of extraction results
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def extract_with_limit(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.extract(url, timeout)
        
        tasks = [extract_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "data": {"url": url},
                    "methods_tried": [],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results


__all__ = [
    "ArticleExtractor",
    "BaseExtractor",
    "TrafilaturaExtractor",
    "NewspaperExtractor",
    "BS4Extractor",
    "PlaywrightExtractor",
]
