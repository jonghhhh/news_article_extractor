# extractor.py - 뉴스 기사 추출 (trafilatura → newspaper3k → playwright)

import re
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List
from collections import OrderedDict
import trafilatura
from newspaper import Article
from playwright.sync_api import sync_playwright


class ArticleExtractor:
    """뉴스 기사 추출기 - 3단계 fallback 전략"""

    @staticmethod
    def _fetch_with_headers(url: str) -> str:
        """커스텀 HTTP 헤더로 페이지 다운로드"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # UTF-8로 직접 디코딩 (인코딩 문제 방지)
        # response.text 대신 response.content를 UTF-8로 디코딩
        try:
            return response.content.decode('utf-8')
        except UnicodeDecodeError:
            # UTF-8 실패 시 apparent_encoding 시도
            if response.apparent_encoding:
                try:
                    return response.content.decode(response.apparent_encoding)
                except:
                    pass
            # 최후의 수단: errors='replace'로 디코딩
            return response.content.decode('utf-8', errors='replace')

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

            # 배너/썸네일 제외: 가로 세로 비율 확인
            # 너무 가늘거나 너무 넓은 이미지 제외 (배너 형식)
            size_pattern = re.search(r'(_ir_)?(\d+)x(\d+)', img_url)
            if size_pattern:
                width, height = int(size_pattern.group(2)), int(size_pattern.group(3))
                
                # 최소 크기: 가로세로 모두 300 이상 (기사 본문 이미지 기준)
                if width < 300 or height < 300:
                    continue
                
                # 가로세로 비율이 너무 극단적이면 제외 (배너: 640x120 등)
                # 비율이 5:1 이상이거나 1:5 이상이면 배너로 간주
                ratio = max(width, height) / min(width, height)
                if ratio > 5:
                    continue

            filtered.append(img_url)

        return filtered

    @staticmethod
    def _extract_images_with_priority(soup, url: str) -> List[str]:
        """우선순위 기반 이미지 추출 (og:image → article 이미지 → 일반 이미지)"""
        from urllib.parse import urljoin
        images = []

        # 1순위: og:image 메타태그 (가장 정확한 대표 이미지)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image.get('content')
            if img_url.startswith('http'):
                images.append(img_url)
            else:
                images.append(urljoin(url, img_url))

        # 2순위: twitter:image 메타태그
        tw_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if tw_image and tw_image.get('content'):
            img_url = tw_image.get('content')
            if img_url not in images:
                if img_url.startswith('http'):
                    images.append(img_url)
                else:
                    images.append(urljoin(url, img_url))

        # 3순위: article 내부 이미지 (한국 뉴스 사이트 패턴)
        selectors = [
            'article img[src]',
            '.article-body img[src]',
            '.article_body img[src]',
            '#article img[src]',
            '#articleBody img[src]',
            '.news_view img[src]',  # 네이버
            '.view_content img[src]',  # 다음
            '.article_view img[src]',  # 일반 뉴스
        ]

        for selector in selectors:
            for img in soup.select(selector):
                src = img.get('src') or img.get('data-src')
                if src:
                    if src.startswith('http'):
                        img_url = src
                    else:
                        img_url = urljoin(url, src)
                    if img_url not in images:
                        images.append(img_url)

        # 4순위: 일반 img 태그 (fallback, 최대 10개만 수집)
        if len(images) < 5:
            for img in soup.find_all('img', src=True, limit=30):
                src = img.get('src') or img.get('data-src')
                if src:
                    if src.startswith('http'):
                        img_url = src
                    else:
                        img_url = urljoin(url, src)
                    if img_url not in images:
                        images.append(img_url)
                        if len(images) >= 10:
                            break

        # 중복 제거 (순서 유지)
        images = list(OrderedDict.fromkeys(images))

        # 필터링 적용
        return ArticleExtractor._filter_images(images)

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
    def extract(url: str) -> Dict:
        """
        URL에서 기사 정보를 추출합니다.

        우선순위:
        1. trafilatura (빠름, 정확)
        2. newspaper3k (중간)
        3. playwright (느림, 확실)

        부분 병합 전략: 각 방법에서 추출된 정보를 누적하여 완성도를 높임

        Returns:
            {
                "url": str,
                "title": str,
                "text": str,
                "date": str,
                "images": List[str],
                "method": str  # 사용된 추출 방법 (쉼표로 구분)
            }
        """
        result = {
            "url": url,
            "title": "",
            "text": "",
            "date": "",
            "images": [],
            "method": []
        }

        # 1단계: trafilatura 시도
        try:
            data = ArticleExtractor._extract_with_trafilatura(url)
            if data:
                if data.get("title"):
                    result["title"] = data["title"]
                if data.get("text"):
                    result["text"] = data["text"]
                if data.get("date"):
                    result["date"] = data["date"]
                if data.get("images"):
                    result["images"].extend(data["images"])
                result["method"].append("trafilatura")

                # 충분한 정보를 얻었으면 조기 종료
                if result["title"] and result["text"] and len(result["images"]) >= 1:
                    result["method"] = ", ".join(result["method"])
                    result["images"] = list(OrderedDict.fromkeys(result["images"]))[:5]
                    return result
        except Exception as e:
            print(f"Trafilatura failed: {str(e)}")

        # 2단계: newspaper3k로 부족한 부분 보완
        if not result["title"] or not result["text"] or not result["images"]:
            try:
                data = ArticleExtractor._extract_with_newspaper(url)
                if data:
                    if not result["title"] and data.get("title"):
                        result["title"] = data["title"]
                    if not result["text"] and data.get("text"):
                        result["text"] = data["text"]
                    if not result["date"] and data.get("date"):
                        result["date"] = data["date"]
                    if data.get("images"):
                        result["images"].extend(data["images"])
                    result["method"].append("newspaper3k")

                    # 충분한 정보를 얻었으면 조기 종료
                    if result["title"] and result["text"] and len(result["images"]) >= 1:
                        result["method"] = ", ".join(result["method"])
                        result["images"] = list(OrderedDict.fromkeys(result["images"]))[:5]
                        return result
            except Exception as e:
                print(f"Newspaper3k failed: {str(e)}")

        # 3단계: playwright로 최종 시도
        if not result["text"]:
            try:
                data = ArticleExtractor._extract_with_playwright(url)
                if data:
                    if not result["title"] and data.get("title"):
                        result["title"] = data["title"]
                    if not result["text"] and data.get("text"):
                        result["text"] = data["text"]
                    if not result["date"] and data.get("date"):
                        result["date"] = data["date"]
                    if data.get("images"):
                        result["images"].extend(data["images"])
                    result["method"].append("playwright")
            except Exception as e:
                print(f"Playwright failed: {str(e)}")

        # 최종 결과 정리
        result["method"] = ", ".join(result["method"]) if result["method"] else "none"
        result["images"] = list(OrderedDict.fromkeys(result["images"]))[:5]

        # 본문이 없으면 실패
        if not result["text"] or len(result["text"]) < 100:
            raise ValueError("모든 추출 방법 실패: 본문을 찾을 수 없습니다")

        return result

    @staticmethod
    def _extract_with_trafilatura(url: str) -> Dict:
        """trafilatura로 추출 (JSON 방식 + 커스텀 헤더)"""
        from bs4 import BeautifulSoup

        # 커스텀 헤더로 HTML 다운로드
        html = ArticleExtractor._fetch_with_headers(url)
        if not html:
            raise ValueError("페이지 다운로드 실패")

        # JSON 포맷으로 한 번에 추출 (제목, 본문, 날짜, 이미지 모두 포함)
        result_json = trafilatura.extract(
            html,
            output_format='json',
            url=url,
            include_comments=False,
            include_tables=False,
            include_images=True,
            include_links=True,
            no_fallback=False,
            date_extraction_params={'extensive_search': True}  # 날짜 추출 강화
        )

        if not result_json:
            return None

        data = json.loads(result_json)

        # BeautifulSoup으로 이미지 우선순위 추출
        soup = BeautifulSoup(html, 'html.parser')
        images = ArticleExtractor._extract_images_with_priority(soup, url)

        # Trafilatura가 찾은 이미지도 추가 (있으면)
        if data.get('image'):
            if data['image'] not in images:
                images.insert(0, data['image'])

        # 날짜가 없으면 fallback
        date = data.get('date') or ArticleExtractor._extract_date(soup, url)

        return {
            "url": url,
            "title": data.get('title', ''),
            "text": data.get('text', ''),
            "date": date,
            "images": images[:5]  # 최대 5개
        }

    @staticmethod
    def _extract_with_newspaper(url: str) -> Dict:
        """newspaper3k로 추출 (HTML 재사용 + 우선순위 이미지)"""
        from bs4 import BeautifulSoup

        # 커스텀 헤더로 HTML 다운로드 (trafilatura와 동일한 HTML 재사용)
        html = ArticleExtractor._fetch_with_headers(url)

        # Newspaper3k로 파싱
        article = Article(url, language='ko')
        article.set_html(html)  # 다운로드하지 않고 HTML 주입
        article.parse()

        # 우선순위 기반 이미지 추출
        soup = BeautifulSoup(html, 'html.parser')
        images = ArticleExtractor._extract_images_with_priority(soup, url)

        # Newspaper3k가 찾은 top_image도 추가
        if article.top_image and article.top_image not in images:
            images.insert(0, article.top_image)

        # 날짜 처리
        date = article.publish_date.isoformat() if article.publish_date else ""

        # 날짜가 없으면 fallback
        if not date:
            date = ArticleExtractor._extract_date(soup, url)

        return {
            "url": url,
            "title": article.title,
            "text": article.text,
            "date": date,
            "images": images[:5]
        }

    @staticmethod
    def _extract_with_playwright(url: str) -> Dict:
        """playwright로 추출 (news_text_scraper_1.py 참조)"""
        from bs4 import BeautifulSoup
        from readability import Document
        import time
        import os
        import traceback

        try:
            with sync_playwright() as p:
                # Render 환경 감지 (PORT 환경 변수로 감지)
                is_production = os.getenv('PORT') is not None

                # Render 환경에 최적화된 Chromium 옵션 (필수)
                browser_args = [
                    '--no-sandbox',  # 필수: Render 환경에서 sandbox 불가
                    '--disable-setuid-sandbox',  # 필수: 권한 문제 회피
                    '--disable-dev-shm-usage',  # 필수: /dev/shm 제한 회피
                    '--disable-gpu',  # GPU 비활성화
                    '--disable-software-rasterizer',  # SW 렌더러 비활성화
                    '--disable-features=IsolateOrigins,site-per-process',  # 격리 기능 비활성화
                ]

                # 프로덕션 환경(Render)에서만 추가 최적화
                if is_production:
                    browser_args.extend([
                        '--single-process',  # 메모리 절약
                        '--no-zygote',  # zygote 프로세스 비활성화
                        '--disable-accelerated-2d-canvas',  # 2D 캔버스 가속 비활성화
                        '--disable-background-timer-throttling',
                    ])
                    print("[Playwright] Running in PRODUCTION mode")
                else:
                    print("[Playwright] Running in LOCAL mode")

                print(f"[Playwright] Launching Chromium with {len(browser_args)} args")

                browser = p.chromium.launch(
                    headless=True,
                    args=browser_args
                )
                print("[Playwright] Chromium launched successfully")

                try:
                    # context를 사용하여 설정 관리 (안정성 향상)
                    print(f"[Playwright] Creating browser context for: {url}")
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        viewport={'width': 1920, 'height': 1080}  # 반응형 렌더링
                    )
                    page = context.new_page()

                    # 타임아웃 30초
                    print(f"[Playwright] Navigating to {url}")
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    print("[Playwright] Page loaded successfully")

                    # 동적 로딩 대기
                    time.sleep(2)

                    # 스크롤 (필요시)
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(0.5)
                    except Exception as scroll_error:
                        print(f"[Playwright] Scroll error (non-critical): {str(scroll_error)}")

                    html = page.content()
                    print(f"[Playwright] HTML extracted: {len(html)} bytes")
                finally:
                    browser.close()
                    print("[Playwright] Browser closed")

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

            # 우선순위 기반 이미지 추출
            images = ArticleExtractor._extract_images_with_priority(soup, url)

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

        except Exception as e:
            print(f"[Playwright] ERROR: Extraction failed for {url}")
            print(f"[Playwright] Error: {str(e)}")
            print(f"[Playwright] Traceback:")
            traceback.print_exc()
            raise

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
