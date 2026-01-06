"""
Base extractor class with common interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import re
from urllib.parse import urlparse
from datetime import datetime


class BaseExtractor(ABC):
    """Abstract base class for article extractors"""
    
    name: str = "base"
    
    @abstractmethod
    async def extract(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Extract article data from URL
        
        Args:
            url: Article URL
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with extracted data or None if failed
        """
        pass
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text"""
        if not text:
            return None
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text if text else None
    
    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse and normalize date string to ISO format"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
            "%Y.%m.%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        
        # Clean the date string
        date_str = date_str.strip()
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # Return original if parsing fails
        return date_str
    
    def extract_numbers(self, text: Optional[str]) -> Optional[int]:
        """Extract numbers from text (for view counts, etc.)"""
        if not text:
            return None
        
        # Remove commas and extract numbers
        text = text.replace(",", "").replace(".", "")
        numbers = re.findall(r'\d+', text)
        
        if numbers:
            return int(numbers[0])
        return None
    
    def normalize_url(self, url: Optional[str], base_url: str) -> Optional[str]:
        """Normalize relative URLs to absolute"""
        if not url:
            return None
        
        if url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        elif not url.startswith("http"):
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}/{url}"
        
        return url
