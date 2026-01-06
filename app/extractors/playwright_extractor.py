"""
Playwright-based article extractor
For JavaScript-heavy sites that require full rendering
"""
import asyncio
from typing import Optional, Dict, Any, List
import re
import json
from .base import BaseExtractor


class PlaywrightExtractor(BaseExtractor):
    """
    Playwright extractor - Fourth fallback for JS-rendered sites
    Handles dynamic content that requires browser rendering
    """
    
    name = "playwright"
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Extract article using Playwright with full browser rendering"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                    ]
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="ko-KR",
                )
                
                page = await context.new_page()
                
                try:
                    # Navigate and wait for content
                    await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
                    
                    # Wait for common article selectors
                    await self._wait_for_content(page)
                    
                    # Get page content
                    html = await page.content()
                    
                    # Extract data from rendered page
                    data = await self._extract_from_page(page, url)
                    
                    # Also try trafilatura on rendered HTML for content
                    content_data = await self._extract_content_trafilatura(html, url)
                    
                    # Merge data
                    if content_data:
                        data.update({k: v for k, v in content_data.items() if v and not data.get(k)})
                    
                    data["extraction_method"] = self.name
                    
                    return data
                    
                finally:
                    await browser.close()
                    
        except ImportError:
            print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            print(f"Playwright extraction failed: {e}")
            return None
    
    async def _wait_for_content(self, page) -> None:
        """Wait for article content to load"""
        selectors = [
            "article",
            "[itemprop='articleBody']",
            ".article-content",
            ".article-body",
            "#article-body",
            ".news_view",
            ".article_view",
        ]
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                return
            except:
                continue
    
    async def _extract_from_page(self, page, url: str) -> Dict[str, Any]:
        """Extract data directly from page using JavaScript"""
        
        data = await page.evaluate(r"""() => {
            const result = {
                title: null,
                content: null,
                summary: null,
                published_date: null,
                author: null,
                main_image_url: null,
                image_urls: [],
                video_url: null,
                video_urls: [],
                category: null,
                tags: [],
                view_count: null,
                like_count: null,
                comment_count: null,
                source_name: null,
                og_title: null,
                og_description: null,
                og_image: null,
            };
            
            // Title
            const titleSelectors = [
                'h1.article-title', 'h1.entry-title', 'h1.post-title',
                'article h1', 'main h1', '.headline h1', 'h1[itemprop="headline"]',
                'h2.tit_view', 'h1.news_title', 'h1'
            ];
            for (const sel of titleSelectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent.trim()) {
                    result.title = el.textContent.trim();
                    break;
                }
            }
            
            // Content
            const contentSelectors = [
                'article[itemprop="articleBody"]', 'div[itemprop="articleBody"]',
                '.article-content', '.article-body', '.entry-content',
                '#article-body', '.news_view', '.article_view', 'article'
            ];
            for (const sel of contentSelectors) {
                const el = document.querySelector(sel);
                if (el) {
                    // Clone and remove unwanted elements
                    const clone = el.cloneNode(true);
                    clone.querySelectorAll('script, style, aside, nav, footer, iframe, .ad, .advertisement').forEach(e => e.remove());
                    const text = clone.textContent.trim();
                    if (text.length > 200) {
                        result.content = text;
                        break;
                    }
                }
            }
            
            // Meta tags
            const getMeta = (name) => {
                const el = document.querySelector(`meta[property="${name}"], meta[name="${name}"]`);
                return el ? el.getAttribute('content') : null;
            };
            
            result.og_title = getMeta('og:title');
            result.og_description = getMeta('og:description');
            result.og_image = getMeta('og:image');
            result.summary = getMeta('description') || result.og_description;
            result.source_name = getMeta('og:site_name');
            result.published_date = getMeta('article:published_time') || getMeta('datePublished');
            
            // Author
            const authorSelectors = ['.author', '.byline', '[rel="author"]', '[itemprop="author"]', '.reporter'];
            for (const sel of authorSelectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent.trim()) {
                    result.author = el.textContent.trim();
                    break;
                }
            }
            
            // Date
            const dateEl = document.querySelector('time[datetime]');
            if (dateEl) {
                result.published_date = dateEl.getAttribute('datetime');
            }
            
            // Images
            const mainImg = getMeta('og:image');
            if (mainImg) result.main_image_url = mainImg;
            
            document.querySelectorAll('article img, .article-content img, .article-body img').forEach(img => {
                const src = img.src || img.dataset.src;
                if (src && !src.includes('icon') && !src.includes('logo')) {
                    result.image_urls.push(src);
                }
            });
            result.image_urls = [...new Set(result.image_urls)].slice(0, 10);
            
            // Videos
            document.querySelectorAll('video source, video').forEach(v => {
                const src = v.src || v.querySelector('source')?.src;
                if (src) result.video_urls.push(src);
            });
            document.querySelectorAll('iframe').forEach(iframe => {
                const src = iframe.src;
                if (src && (src.includes('youtube') || src.includes('vimeo') || src.includes('video'))) {
                    result.video_urls.push(src);
                }
            });
            result.video_urls = [...new Set(result.video_urls)];
            if (result.video_urls.length > 0) result.video_url = result.video_urls[0];
            
            // Category
            const categorySelectors = ['.category', '[itemprop="articleSection"]', '.section'];
            for (const sel of categorySelectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent.trim()) {
                    result.category = el.textContent.trim();
                    break;
                }
            }
            
            // Tags
            const keywordsMeta = getMeta('keywords') || getMeta('news_keywords');
            if (keywordsMeta) {
                result.tags = keywordsMeta.split(',').map(t => t.trim()).filter(t => t);
            }
            
            // Stats (best effort)
            const extractNumber = (text) => {
                if (!text) return null;
                const num = text.replace(/[,\.]/g, '').match(/\d+/);
                return num ? parseInt(num[0]) : null;
            };
            
            const viewEl = document.querySelector('[class*="view"], [class*="hit"], [class*="read"]');
            if (viewEl) result.view_count = extractNumber(viewEl.textContent);
            
            const likeEl = document.querySelector('[class*="like"], [class*="recommend"]');
            if (likeEl) result.like_count = extractNumber(likeEl.textContent);
            
            const commentEl = document.querySelector('[class*="comment"], [class*="reply"]');
            if (commentEl) result.comment_count = extractNumber(commentEl.textContent);
            
            return result;
        }""")
        
        data["url"] = url
        data["source_domain"] = self.get_domain(url)
        
        return data
    
    async def _extract_content_trafilatura(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Use trafilatura on rendered HTML for better content extraction"""
        try:
            import trafilatura
            
            result = trafilatura.extract(
                html,
                url=url,
                output_format='json',
                include_comments=False,
                include_tables=True,
                with_metadata=True,
                favor_precision=True,
            )
            
            if result:
                data = json.loads(result)
                return {
                    "content": data.get("text"),
                    "title": data.get("title"),
                    "author": data.get("author"),
                    "published_date": data.get("date"),
                }
        except:
            pass
        
        return None
