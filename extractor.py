# extractor.py - 뉴스 기사 추출 (trafilatura → newspaper3k → playwright)

import re
from datetime import datetime
from typing import Optional, Dict, List
import trafilatura
from newspaper import Article
from playwright.async_api import async_playwright


class ArticleExtractor:
    """뉴스 기사 추출기 - 3단계 fallback 전략"""

    @staticmethod
    def _filter_images(images: List[str]) -> List[str]:
        """로고, 배너, 작은 이미지 필터링 (실제 기사 이미지만 추출)"""
        import re
        filtered = []
        exclude_patterns = [
            '/logo', '_logo', 'logo_', '/icon', '/btn_', '/banner/', '/ad_', '/ads/',
            '/thumb', '/profile', '/avatar', '/emoji', '/symbol', 'office_logo',
            'default', 'placeholder', 'no_image', 'noimage', 'mannerbot', 'people_default'
        ]

        for img_url in images:
            img_lower = img_url.lower()

            # SVG/GIF 파일 제외 (대부분 아이콘/로고/애니메이션)
            if img_url.endswith(('.svg', '.gif')):
                continue

            # 제외 패턴 체크
            if any(pattern in img_lower for pattern in exclude_patterns):
                continue

            # 파일명에 특정 키워드 있으면 제외
            if any(keyword in img_lower for keyword in ['kakao', 'facebook', 'twitter', 'share', 'sns', 'ic-']):
                continue

            # 매우 작은 이미지 크기 패턴 제외 (예: 1x1, 10x10)
            size_pattern = re.search(r'(\d+)x(\d+)', img_url)
            if size_pattern:
                width, height = int(size_pattern.group(1)), int(size_pattern.group(2))
                if width < 100 or height < 100:
                    continue

            filtered.append(img_url)

        return filtered


    @staticmethod
    def _extract_date(soup, url: str, metadata=None) -> str:
        """날짜 추출 - 다양한 방법 시도"""
        # 1. 메타데이터 우선
        if metadata and hasattr(metadata, 'date') and metadata.date:
            return metadata.date

        # 2. meta 태그들 체크
        date_meta_tags = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'article:published_time'}),
            ('meta', {'property': 'og:article:published_time'}),
            ('meta', {'name': 'pubdate'}),
            ('meta', {'name': 'publishdate'}),
            ('meta', {'property': 'datePublished'}),
        ]

        for tag, attrs in date_meta_tags:
            elem = soup.find(tag, attrs)
            if elem and elem.get('content'):
                return elem.get('content')

        # 3. time 태그
        time_elem = soup.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return datetime_attr

        # 4. 네이버 뉴스 특별 처리
        if 'naver.com' in url:
            naver_date = soup.select_one('span.media_end_head_info_datestamp_time')
            if naver_date:
                date_text = naver_date.get('data-date-time', '')
                if date_text:
                    return date_text

        # 5. URL 패턴에서 날짜 추출 시도 (YYYYMMDD)
        date_pattern = re.search(r'/(\d{4})[-/]?(\d{2})[-/]?(\d{2})', url)
        if date_pattern:
            year, month, day = date_pattern.groups()
            return f"{year}-{month}-{day}"

        return ""

    @staticmethod
    async def extract(url: str) -> Dict:
        """
        URL에서 기사 정보를 추출합니다.

        우선순위:
        1. trafilatura (빠름, 정확)
        2. newspaper3k (중간)
        3. playwright (느림, 확실)

        Returns:
            {
                "url": str,
                "title": str,
                "text": str,
                "date": str,
                "images": List[str],
                "method": str  # 사용된 추출 방법
            }
        """
        # 1단계: trafilatura 시도
        try:
            result = await ArticleExtractor._extract_with_trafilatura(url)
            if result and len(result.get("text", "")) > 100:
                result["method"] = "trafilatura"
                return result
        except Exception as e:
            print(f"Trafilatura failed: {e}")

        # 2단계: newspaper3k 시도
        try:
            result = await ArticleExtractor._extract_with_newspaper(url)
            if result and len(result.get("text", "")) > 100:
                result["method"] = "newspaper3k"
                return result
        except Exception as e:
            print(f"Newspaper3k failed: {e}")

        # 3단계: playwright 시도 (최종)
        try:
            result = await ArticleExtractor._extract_with_playwright(url)
            if result and len(result.get("text", "")) > 100:
                result["method"] = "playwright"
                return result
        except Exception as e:
            print(f"Playwright failed: {e}")

        raise ValueError("모든 추출 방법 실패: 본문을 찾을 수 없습니다")

    @staticmethod
    async def _extract_with_trafilatura(url: str) -> Dict:
        """trafilatura로 추출"""
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError("페이지 다운로드 실패")

        # 본문 추출
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )

        # 메타데이터 추출
        metadata = trafilatura.extract_metadata(downloaded)

        # 이미지 추출
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')

        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                images.append(src)

        # 필터링 적용
        images = ArticleExtractor._filter_images(images)

        # 날짜 추출
        date = ArticleExtractor._extract_date(soup, url, metadata)

        return {
            "url": url,
            "title": metadata.title if metadata else "",
            "text": text or "",
            "date": date,
            "images": images[:5]  # 최대 5개
        }

    @staticmethod
    async def _extract_with_newspaper(url: str) -> Dict:
        """newspaper3k로 추출"""
        article = Article(url, language='ko')
        article.download()
        article.parse()

        # 이미지 필터링
        images = ArticleExtractor._filter_images(list(article.images))

        # 날짜 처리
        date = article.publish_date.isoformat() if article.publish_date else ""

        return {
            "url": url,
            "title": article.title,
            "text": article.text,
            "date": date,
            "images": images[:5]
        }

    @staticmethod
    async def _extract_with_playwright(url: str) -> Dict:
        """playwright로 추출 (url_text_extractor 참조)"""
        from bs4 import BeautifulSoup
        from readability import Document

        async with async_playwright() as p:
            # 제한된 환경(Render)에서 Chromium 실행을 위한 설정
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-dev-tools',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-breakpad',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--force-color-profile=srgb',
                    '--hide-scrollbars',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-first-run',
                    '--disable-web-security',
                    '--single-process'  # 메모리 절약을 위한 단일 프로세스
                ]
            )

            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )

                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                await page.wait_for_timeout(1000)
                # 스크롤은 필요시만 (메모리 절약)
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(500)
                except:
                    pass

                html = await page.content()
            finally:
                await browser.close()

        # Readability로 본문 추출
        soup = BeautifulSoup(html, "lxml")

        # 네이버 뉴스 특별 처리
        text = ""
        title = ""
        if "naver.com" in url:
            article_elem = soup.select_one("#dic_area")
            title_elem = soup.select_one("h2.media_end_head_headline, h1")

            if article_elem:
                for tag in article_elem(["script", "style", "noscript"]):
                    tag.decompose()
                text = article_elem.get_text("\n").strip()

            if title_elem:
                title = title_elem.get_text().strip()

        # Readability fallback
        if not text or len(text) < 100:
            doc = Document(html)
            article_html = doc.summary(html_partial=True)
            soup_article = BeautifulSoup(article_html, "lxml")

            for tag in soup_article(["script", "style", "noscript"]):
                tag.decompose()

            text = soup_article.get_text("\n").strip()
            title = doc.title()

        # 이미지 추출
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                images.append(src)

        # 필터링 적용
        images = ArticleExtractor._filter_images(images)

        # 날짜 추출 (개선된 메서드 사용)
        date = ArticleExtractor._extract_date(soup, url)

        # 텍스트 정제
        text = ArticleExtractor._clean_text(text)

        return {
            "url": url,
            "title": title,
            "text": text,
            "date": date,
            "images": images[:5]
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        """텍스트 정제"""
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(k in line for k in ["무단 전재", "재배포 금지", "ⓒ", "Copyright", "▶"]):
                continue
            lines.append(line)

        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
