# 📰 News Article Extractor

뉴스 기사에서 본문, 날짜, 이미지, 영상을 추출하는 간단한 API 서비스입니다.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 주요 기능

- **3단계 추출 전략**: trafilatura → newspaper3k → playwright (자동 fallback)
- **스마트 필터링**: 로고, 배너, 추적 스크립트 자동 제거
- **날짜 추출**: 다양한 메타 태그 및 URL 패턴 지원
- **웹 UI**: 간단한 테스트 인터페이스 제공
- **REST API**: POST/GET 엔드포인트

## 📋 추출 정보

| 필드 | 설명 |
|------|------|
| `url` | 기사 URL |
| `title` | 기사 제목 |
| `text` | 기사 본문 |
| `date` | 발행일 (YYYY-MM-DD) |
| `images` | 이미지 URL 목록 (최대 5개) |
| `videos` | 영상 URL 목록 (최대 3개) |
| `method` | 사용된 추출 방법 |

## 🚀 빠른 시작

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 접속

## 📖 API 사용법

### 웹 UI
브라우저에서 `http://localhost:8000` 접속하여 URL 입력

### POST 방식
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://n.news.naver.com/article/422/0000819667"}'
```

### GET 방식
```bash
curl "http://localhost:8000/extract?url=https://n.news.naver.com/article/422/0000819667"
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
  "videos": [],
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

### 이미지 필터링
- 로고, 배너, 아이콘 제외
- SVG 파일 제외
- SNS 공유 버튼 제외
- 예: `btn_kakao.svg`, `office_logo` 등

### 영상 필터링
- 추적 스크립트 제외 (googletagmanager.com, analytics 등)
- `about:blank` 제외
- YouTube, Vimeo, mp4 등 유효한 영상만 포함

### 날짜 추출
- 메타 태그 우선 (article:published_time, og:article:published_time 등)
- `<time>` HTML 태그
- 네이버 뉴스 특별 처리
- URL 패턴 매칭 (YYYY-MM-DD, YYYYMMDD)

## 📁 프로젝트 구조

```
news_article_extractor/
├── main.py              # FastAPI 애플리케이션 + 웹 UI
├── extractor.py         # ArticleExtractor 클래스
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── README.md
```

## 🐳 Docker 배포

### 로컬 Docker 실행
```bash
docker build -t news-extractor .
docker run -p 8000:8000 news-extractor
```

### Render 배포

1. GitHub 저장소와 연결
2. **Web Service** 선택
3. 배포 설정:
   - **Environment**: Docker
   - **Dockerfile Path**: `news_article_extractor/Dockerfile`
   - **Port**: 8000 (자동 감지)

Render는 `PORT` 환경 변수를 자동으로 설정하므로 별도 설정 불필요.

## 🛠️ 기술 스택

- **FastAPI**: 웹 프레임워크
- **trafilatura**: 빠른 본문 추출
- **newspaper3k**: 한국어 최적화
- **Playwright**: JS 렌더링
- **BeautifulSoup**: HTML 파싱
- **lxml**: XML/HTML 처리
- **Pydantic**: 데이터 검증

## 📄 라이선스

MIT License
