# 📰 News Article Extractor

뉴스 기사 URL에서 제목, 본문, 날짜, 기자, 이미지, 영상 등 다양한 정보를 자동으로 추출하는 웹 서비스입니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 주요 기능

- **다중 추출 엔진**: Trafilatura, Newspaper3k, BeautifulSoup, Playwright 지원
- **자동 폴백 메커니즘**: 하나의 방법이 실패하면 자동으로 다음 방법 시도
- **한국 언론사 최적화**: 네이버뉴스, 다음뉴스, 조선일보, 중앙일보, 한겨레, KBS, MBC, SBS 등
- **방송 기사 영상 추출**: 영상 URL 자동 감지 및 추출
- **JSON Flat Key 구조**: 일관된 평면 구조의 JSON 출력
- **웹 UI 제공**: 직관적인 웹 인터페이스
- **RESTful API**: 다양한 엔드포인트 제공

## 📋 추출 가능한 정보

| 필드 | 설명 |
|------|------|
| `title` | 기사 제목 |
| `content` | 기사 본문 |
| `summary` | 기사 요약 |
| `published_date` | 발행일 |
| `modified_date` | 수정일 |
| `author` | 기자/작성자 |
| `authors` | 기자/작성자 목록 |
| `main_image_url` | 대표 이미지 URL |
| `image_urls` | 본문 이미지 URL 목록 |
| `video_url` | 영상 URL (방송 기사) |
| `video_urls` | 영상 URL 목록 |
| `category` | 카테고리/섹션 |
| `tags` | 태그/키워드 |
| `view_count` | 조회수 |
| `like_count` | 좋아요 수 |
| `comment_count` | 댓글 수 |
| `source_name` | 언론사명 |
| `source_domain` | 언론사 도메인 |
| `language` | 언어 |
| `og_title` | Open Graph 제목 |
| `og_description` | Open Graph 설명 |
| `og_image` | Open Graph 이미지 |

## 🚀 빠른 시작

### 요구사항

- Python 3.9 이상
- pip

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/news-article-extractor.git
cd news-article-extractor

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# nltk 데이터 다운로드 (newspaper3k용)
python -c "import nltk; nltk.download('punkt')"
```

### Playwright 설치 (선택사항)

JavaScript 렌더링이 필요한 사이트를 위해 Playwright를 설치합니다:

```bash
pip install playwright
playwright install chromium
```

### 실행

```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 접속

## 📖 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API 엔드포인트

#### GET /api/extract

URL에서 기사를 추출합니다.

```bash
curl "http://localhost:8000/api/extract?url=https://news.example.com/article/12345"
```

**파라미터:**
- `url` (필수): 추출할 기사 URL
- `timeout` (선택): 타임아웃 초 (기본: 30)
- `use_js` (선택): JavaScript 렌더링 사용 여부 (기본: false)

#### POST /api/extract

Request Body로 기사를 추출합니다.

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.example.com/article/12345", "timeout": 30}'
```

#### POST /api/extract/batch

여러 URL을 일괄 추출합니다.

```bash
curl -X POST "http://localhost:8000/api/extract/batch" \
  -H "Content-Type: application/json" \
  -d '["https://news.example.com/1", "https://news.example.com/2"]'
```

#### POST /api/extract/save

기사를 추출하고 JSON 파일로 저장합니다.

```bash
curl -X POST "http://localhost:8000/api/extract/save?url=https://news.example.com/article/12345"
```

## 🔧 추출 엔진

### 추출 순서 및 특징

1. **Trafilatura** (1순위)
   - 가장 빠르고 정확한 추출
   - 대부분의 뉴스 사이트에서 잘 작동
   - 메타데이터 추출 우수

2. **Newspaper3k** (2순위)
   - 표준 뉴스 기사 형식에 최적화
   - NLP 기반 키워드 추출
   - 이미지 추출 우수

3. **BeautifulSoup** (3순위)
   - 한국 언론사별 맞춤 패턴
   - 세밀한 제어 가능
   - 통계 정보 추출 (조회수, 좋아요 등)

4. **Playwright** (4순위, 선택)
   - JavaScript 렌더링 필요 시
   - 동적 콘텐츠 처리
   - 가장 느리지만 가장 확실

### 지원 언론사 (최적화)

한국 언론사:
- 네이버 뉴스 (n.news.naver.com)
- 다음 뉴스 (v.daum.net)
- 조선일보 (www.chosun.com)
- 중앙일보 (www.joongang.co.kr)
- 한겨레 (www.hani.co.kr)
- 동아일보 (www.donga.com)
- KBS (news.kbs.co.kr)
- MBC (imnews.imbc.com)
- SBS (news.sbs.co.kr)
- JTBC (news.jtbc.co.kr)
- YTN (www.ytn.co.kr)

## 📁 프로젝트 구조

```
news-article-extractor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션
│   ├── models.py            # Pydantic 모델
│   └── extractors/
│       ├── __init__.py      # 통합 추출 엔진
│       ├── base.py          # 기본 추출기 클래스
│       ├── trafilatura_extractor.py
│       ├── newspaper_extractor.py
│       ├── bs4_extractor.py
│       └── playwright_extractor.py
├── static/
│   └── index.html           # 웹 UI
├── data/                    # 저장된 JSON 파일
├── requirements.txt
├── README.md
├── Dockerfile
└── docker-compose.yml
```

## 🐳 Docker 사용

### Docker로 실행

```bash
# 이미지 빌드
docker build -t news-extractor .

# 컨테이너 실행
docker run -p 8000:8000 news-extractor
```

### Docker Compose로 실행

```bash
docker-compose up -d
```

## 📝 응답 예시

```json
{
  "success": true,
  "data": {
    "url": "https://news.example.com/article/12345",
    "title": "기사 제목 예시",
    "content": "기사 본문 내용이 여기에 표시됩니다...",
    "summary": "기사 요약 내용",
    "published_date": "2024-01-15T10:30:00",
    "author": "홍길동 기자",
    "authors": ["홍길동 기자"],
    "main_image_url": "https://example.com/images/main.jpg",
    "image_urls": [
      "https://example.com/images/1.jpg",
      "https://example.com/images/2.jpg"
    ],
    "video_url": null,
    "video_urls": null,
    "category": "정치",
    "tags": ["정치", "국회", "법안"],
    "view_count": 12345,
    "like_count": 234,
    "comment_count": 56,
    "source_name": "예시뉴스",
    "source_domain": "news.example.com",
    "language": "ko",
    "extraction_method": "trafilatura",
    "extraction_time": "2024-01-15T15:30:45.123456"
  },
  "methods_tried": ["trafilatura"],
  "error": null
}
```

## ⚙️ 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `HOST` | 서버 호스트 | `0.0.0.0` |
| `PORT` | 서버 포트 | `8000` |
| `LOG_LEVEL` | 로그 레벨 | `info` |
| `STORAGE_DIR` | 저장 디렉토리 | `./data` |

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:

- [Trafilatura](https://github.com/adbar/trafilatura)
- [Newspaper3k](https://github.com/codelucas/newspaper)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Playwright](https://playwright.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
