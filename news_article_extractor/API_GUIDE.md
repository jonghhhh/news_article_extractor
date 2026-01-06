# News Article Extractor API 사용 가이드

## 목차
- [시작하기](#시작하기)
- [API 엔드포인트](#api-엔드포인트)
- [사용 예제](#사용-예제)
- [응답 형식](#응답-형식)
- [에러 처리](#에러-처리)

---

## 시작하기

### 서버 실행

```bash
# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 서버 실행
python run.py
```

서버가 실행되면 다음 주소로 접속할 수 있습니다:
- **웹 인터페이스**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API 엔드포인트

### 1. 기사 추출 API

**엔드포인트**: `POST /api/extract`

외부 사용자가 뉴스 기사 URL만 입력하면 자동으로 기사 정보를 추출합니다.

#### 요청 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `url` | string | ✅ | 추출할 뉴스 기사 URL |
| `extractor` | string | ❌ | 추출기 선택 (기본값: `all`) |

#### 추출기 옵션

- `all`: 모든 추출기 사용 (기본값, 권장)
- `bs4`: BeautifulSoup4 추출기
- `newspaper`: Newspaper3k 추출기
- `playwright`: Playwright 추출기 (JavaScript 렌더링)
- `trafilatura`: Trafilatura 추출기

---

## 사용 예제

### 1. cURL로 API 호출

```bash
# 기본 사용 (모든 추출기 사용)
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.example.com/article/123"
  }'

# 특정 추출기 지정
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.example.com/article/123",
    "extractor": "newspaper"
  }'
```

### 2. Python으로 API 호출

```python
import requests
import json

# API URL
api_url = "http://localhost:8000/api/extract"

# 요청 데이터
data = {
    "url": "https://news.example.com/article/123"
}

# POST 요청
response = requests.post(api_url, json=data)

# 응답 처리
if response.status_code == 200:
    result = response.json()
    print(f"제목: {result['title']}")
    print(f"저자: {result['authors']}")
    print(f"발행일: {result['publish_date']}")
    print(f"본문: {result['content'][:200]}...")  # 처음 200자만
else:
    print(f"에러: {response.status_code}")
    print(response.json())
```

### 3. JavaScript (Fetch API)로 API 호출

```javascript
// API URL
const apiUrl = 'http://localhost:8000/api/extract';

// 요청 데이터
const data = {
  url: 'https://news.example.com/article/123'
};

// POST 요청
fetch(apiUrl, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(result => {
    console.log('제목:', result.title);
    console.log('저자:', result.authors);
    console.log('발행일:', result.publish_date);
    console.log('본문:', result.content);
  })
  .catch(error => {
    console.error('에러:', error);
  });
```

### 4. Node.js (axios)로 API 호출

```javascript
const axios = require('axios');

async function extractArticle(url) {
  try {
    const response = await axios.post('http://localhost:8000/api/extract', {
      url: url
    });

    const result = response.data;
    console.log('제목:', result.title);
    console.log('저자:', result.authors);
    console.log('발행일:', result.publish_date);
    console.log('본문:', result.content.substring(0, 200) + '...');

    return result;
  } catch (error) {
    console.error('에러:', error.response?.data || error.message);
    throw error;
  }
}

// 사용 예제
extractArticle('https://news.example.com/article/123');
```

---

## 응답 형식

### 성공 응답 (200 OK)

```json
{
  "url": "https://news.example.com/article/123",
  "title": "기사 제목",
  "authors": ["홍길동", "김철수"],
  "publish_date": "2024-01-06T12:00:00",
  "content": "기사 본문 내용...",
  "summary": "기사 요약...",
  "keywords": ["키워드1", "키워드2"],
  "images": ["https://example.com/image1.jpg"],
  "videos": ["https://example.com/video1.mp4"],
  "extractor_used": "newspaper",
  "extraction_time": 1.23
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `url` | string | 요청한 기사 URL |
| `title` | string | 기사 제목 |
| `authors` | array | 저자 목록 |
| `publish_date` | string | 발행일 (ISO 8601 형식) |
| `content` | string | 기사 본문 |
| `summary` | string | 기사 요약 |
| `keywords` | array | 키워드 목록 |
| `images` | array | 이미지 URL 목록 |
| `videos` | array | 비디오 URL 목록 |
| `extractor_used` | string | 사용된 추출기 이름 |
| `extraction_time` | float | 추출 소요 시간 (초) |

---

## 에러 처리

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### 주요 에러 코드

| 상태 코드 | 설명 | 해결 방법 |
|----------|------|----------|
| `400` | 잘못된 요청 | URL 형식을 확인하세요 |
| `404` | 페이지를 찾을 수 없음 | URL이 유효한지 확인하세요 |
| `422` | 유효성 검증 실패 | 요청 파라미터를 확인하세요 |
| `500` | 서버 내부 오류 | 서버 로그를 확인하세요 |

### 에러 처리 예제

```python
import requests

def extract_article_safe(url):
    try:
        response = requests.post(
            "http://localhost:8000/api/extract",
            json={"url": url},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 에러: {e}")
        print(f"응답 내용: {e.response.json()}")
    except requests.exceptions.Timeout:
        print("요청 시간 초과")
    except requests.exceptions.RequestException as e:
        print(f"요청 실패: {e}")

    return None

# 사용 예제
result = extract_article_safe("https://news.example.com/article/123")
if result:
    print(f"성공: {result['title']}")
else:
    print("추출 실패")
```

---

## 실전 사용 예제

### 여러 기사 일괄 추출

```python
import requests
import time

def extract_multiple_articles(urls):
    """여러 기사를 순차적으로 추출"""
    results = []

    for url in urls:
        try:
            response = requests.post(
                "http://localhost:8000/api/extract",
                json={"url": url}
            )

            if response.status_code == 200:
                results.append(response.json())
                print(f"✓ 성공: {url}")
            else:
                print(f"✗ 실패: {url} (상태 코드: {response.status_code})")

            # 서버 부하 방지를 위한 딜레이
            time.sleep(1)

        except Exception as e:
            print(f"✗ 에러: {url} - {e}")

    return results

# 사용 예제
urls = [
    "https://news.example.com/article/123",
    "https://news.example.com/article/456",
    "https://news.example.com/article/789"
]

articles = extract_multiple_articles(urls)
print(f"\n총 {len(articles)}개 기사 추출 완료")
```

### CSV로 저장

```python
import requests
import csv

def save_articles_to_csv(urls, output_file='articles.csv'):
    """추출한 기사를 CSV 파일로 저장"""

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', '제목', '저자', '발행일', '본문'])

        for url in urls:
            response = requests.post(
                "http://localhost:8000/api/extract",
                json={"url": url}
            )

            if response.status_code == 200:
                data = response.json()
                writer.writerow([
                    data['url'],
                    data['title'],
                    ', '.join(data['authors']),
                    data['publish_date'],
                    data['content'][:500]  # 처음 500자만 저장
                ])
                print(f"✓ 저장: {data['title']}")

    print(f"\n{output_file}에 저장 완료")

# 사용 예제
urls = ["https://news.example.com/article/123"]
save_articles_to_csv(urls)
```

---

## 추가 정보

### API 문서 확인

서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 문의 및 버그 리포트

- GitHub: https://github.com/jonghhhh/news_article_extractor
- Issues: https://github.com/jonghhhh/news_article_extractor/issues

---

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다.
