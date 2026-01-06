# 📰 News Article Extractor

뉴스 기사에서 본문, 날짜, 이미지를 추출하는 간단하고 빠른 API 서비스입니다.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

🌐 **Live Demo**: [https://news-article-extractor.onrender.com](https://news-article-extractor.onrender.com)

## ✨ 주요 기능

- **3단계 추출 전략**: trafilatura → newspaper3k → playwright (자동 fallback)
- **강화된 이미지 필터링**: 로고, 배너, GIF, 작은 이미지 자동 제거
- **날짜 추출**: 다양한 메타 태그 및 URL 패턴 지원
- **웹 UI**: Python 코드 예제 포함 인터페이스
- **REST API**: POST/GET 엔드포인트

## 📋 추출 정보

| 필드 | 설명 |
|------|------|
| `url` | 기사 URL |
| `title` | 기사 제목 |
| `text` | 기사 본문 (광고/저작권 문구 제거됨) |
| `date` | 발행일 (YYYY-MM-DD) |
| `images` | 이미지 URL 목록 (최대 5개, 로고/배너/GIF 제외) |
| `method` | 사용된 추출 방법 (trafilatura/newspaper3k/playwright) |

## 🚀 빠른 시작

### Docker Compose 실행 (권장)

```bash
# Docker Compose로 실행
docker-compose up

# 백그라운드 실행
docker-compose up -d
```

브라우저에서 http://localhost:10000 접속

### 직접 실행

```bash
# 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 10000
```

## 📖 API 사용법

### 웹 UI
브라우저에서 https://news-article-extractor.onrender.com 또는 `http://localhost:10000` 접속

웹 UI에서 다음을 확인할 수 있습니다:
- API 사용법 (curl 예제)
- Python 코드 예제 (requests, aiohttp, pandas)
- 제약사항 및 성능 정보
- 완전한 API 문서

### POST 방식
```bash
curl -X POST https://news-article-extractor.onrender.com/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://n.news.naver.com/article/422/0000819667"}'
```

### GET 방식
```bash
curl "https://news-article-extractor.onrender.com/extract?url=https://n.news.naver.com/article/422/0000819667"
```

### 응답 예시
```json
{
  "url": "https://n.news.naver.com/article/422/0000819667",
  "title": "기사 제목",
  "text": "본문 내용...",
  "date": "2026-01-06",
  "images": [
    "https://imgnews.pstatic.net/image/422/2026/01/06/image1.jpg",
    "https://imgnews.pstatic.net/image/422/2026/01/06/image2.jpg"
  ],
  "method": "trafilatura"
}
```

## 🔧 추출 방법

### 1. trafilatura (우선순위 1)
- 가장 빠르고 정확
- 대부분의 뉴스 사이트 지원
- 메타데이터 추출 우수

### 2. newspaper3k (우선순위 2)
- trafilatura 실패 시 시도
- 한국어 지원 우수
- 이미지 추출 강화

### 3. playwright (최종 fallback)
- JavaScript 렌더링 필요한 페이지
- 네이버 뉴스 특별 처리
- 가장 느리지만 확실

## 🎯 필터링 기능

### 강화된 이미지 필터링
실제 기사 이미지만 정확하게 추출하도록 다층 필터링 적용:

- **파일 형식**: SVG, GIF 파일 제외 (로고/아이콘/애니메이션)
- **패턴 제외**: logo, icon, banner, ad, profile, avatar, emoji 등
- **키워드 제외**: kakao, facebook, twitter, share, sns, ic- 접두사
- **특정 이미지**: mannerbot, people_default, placeholder 등 제외
- **크기 필터**: 100x100px 미만 이미지 자동 제외

### 날짜 추출
다양한 방법으로 정확한 날짜 추출:

- **메타 태그 우선**: article:published_time, og:article:published_time 등
- **HTML 태그**: `<time>` 태그의 datetime 속성
- **네이버 뉴스**: 특별 처리 (data-date-time 속성)
- **URL 패턴**: YYYY-MM-DD, YYYYMMDD 형식 자동 인식

## 📁 프로젝트 구조

```
news_article_extractor/
├── main.py              # FastAPI 애플리케이션 + 웹 UI
├── extractor.py         # ArticleExtractor 클래스 (3단계 fallback)
├── requirements.txt     # Python 의존성
├── Dockerfile           # 최적화된 Docker 이미지 (512MB RAM)
├── docker-compose.yml   # 로컬 개발용
├── .dockerignore
├── .gitignore
└── README.md
```

## 🐳 Docker 배포

### 로컬 Docker 실행
```bash
# Docker Compose 사용 (권장)
docker-compose up

# 또는 직접 빌드
docker build -t news-extractor .
docker run -p 10000:10000 news-extractor
```

### Render 배포

현재 Render에서 실행 중: https://news-article-extractor.onrender.com

1. GitHub 저장소와 연결
2. **Web Service** 선택
3. 배포 설정:
   - **Environment**: Docker
   - **Dockerfile Path**: `Dockerfile`
   - **Port**: 자동 감지 (환경 변수 PORT 사용)
4. 플랜:
   - **Starter Plan**: $7/month, 512MB RAM, 0.5 CPU
   - 메모리 최적화: Chromium --single-process 모드

### 성능 최적화

**Render 512MB RAM 환경을 위한 최적화:**
- Chromium 단일 프로세스 모드 (`--single-process`)
- 20+ 메모리 절약 플래그
- 타임아웃 최적화 (20초)
- 메모리 사용량: ~280MB (최대 480MB에서 개선)

## 🛠️ 기술 스택

- **FastAPI**: 웹 프레임워크
- **trafilatura**: 빠른 본문 추출 (우선순위 1)
- **newspaper3k**: 한국어 최적화 (우선순위 2)
- **Playwright**: JavaScript 렌더링 (최종 fallback)
- **BeautifulSoup**: HTML 파싱
- **Readability**: 본문 추출 보조
- **lxml**: XML/HTML 처리
- **Pydantic**: 데이터 검증

## 🌟 지원 사이트

| 사이트 | 상태 | 추출 방법 | 속도 |
|-------|------|-----------|------|
| 네이버 뉴스 | ✅ 빠름 | trafilatura | 2-3초 |
| SBS 뉴스 | ✅ 빠름 | trafilatura | 2-3초 |
| 조선일보 | ⚠️ 느림 | playwright | 15-25초 |
| 해외 언론 | ❌ 불안정 | playwright | 타임아웃 가능 |

**권장사항:**
- 대량 처리(100개 이상)는 로컬 Docker 환경 사용
- Rate limiting 적용 (요청 간 2초 대기)
- 배치 크기 제한 (한 번에 10-50개)

## 📄 라이선스

MIT License

## 🔗 링크

- **Live Demo**: https://news-article-extractor.onrender.com
- **GitHub**: https://github.com/jonghhhh/news_article_extractor
- **API 문서**: https://news-article-extractor.onrender.com/docs
