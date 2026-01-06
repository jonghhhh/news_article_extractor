# 본문 추출 개선 사항

## 변경 내용

### 1. 추출기 우선순위 및 폴백 체인 개선

이제 기사 본문 추출 시 다음 순서로 자동 폴백이 적용됩니다:

1. **Trafilatura** (1순위) - 빠르고 정확한 본문 추출
2. **Newspaper3k** (2순위) - 표준 뉴스 형식에 최적화
3. **BeautifulSoup4** (3순위) - 한국 언론사 커스텀 패턴
4. **Playwright** (4순위) - JavaScript 렌더링으로 동적 페이지 처리

### 2. 본문 추출 검증 강화

추출된 본문이 다음 조건을 만족하지 않으면 자동으로 다음 추출기를 시도합니다:

#### 검증 조건:
- ✅ 제목이 존재하고 비어있지 않아야 함
- ✅ 본문이 **200자 이상**이어야 함
- ✅ 다음과 같은 무효 패턴이 본문의 전부가 아니어야 함:
  - "기사 섹션 분류 안내"
  - "언론사의 분류를 따르고 있습니다"
  - "페이지를 찾을 수 없습니다"
  - "404" / "not found"
  - "접근이 거부되었습니다"

### 3. 기본 설정 변경

- **Playwright 자동 사용**: 이제 기본적으로 Playwright가 폴백 체인에 포함됩니다
- 본문 추출 실패 시 자동으로 더 강력한 추출기로 전환

## 사용 예제

### 자동 폴백 (권장)

```python
import requests

# Playwright까지 자동으로 시도
response = requests.post(
    "http://localhost:8000/api/extract",
    json={"url": "https://news.example.com/article/123"}
)

result = response.json()
print(f"사용된 추출기: {result['methods_tried']}")
print(f"본문 길이: {len(result['data']['content'])} 자")
```

### Playwright 비활성화 (빠른 추출)

```python
# GET 방식으로 호출 (Playwright 제외)
response = requests.get(
    "http://localhost:8000/api/extract",
    params={
        "url": "https://news.example.com/article/123",
        "use_js": False  # Playwright 비활성화
    }
)
```

### 강제로 Playwright 사용

```python
# POST 방식으로 Playwright 강제 사용
response = requests.post(
    "http://localhost:8000/api/extract",
    json={
        "url": "https://news.example.com/article/123",
        "use_javascript": True  # Playwright 우선 사용
    }
)
```

## 추출 결과 예시

### 개선 전
```json
{
  "success": true,
  "data": {
    "title": "기사 제목",
    "content": "기사 섹션 분류 안내 기사의 섹션 정보는...",
    "extractor_used": "trafilatura"
  },
  "methods_tried": ["trafilatura"]
}
```

### 개선 후
```json
{
  "success": true,
  "data": {
    "title": "기사 제목",
    "content": "실제 기사 본문 내용이 200자 이상 제대로 추출됨...",
    "extractor_used": "playwright"
  },
  "methods_tried": ["trafilatura", "newspaper", "bs4", "playwright"]
}
```

## 성능 고려사항

### 추출 속도 비교

| 추출기 | 평균 속도 | 정확도 | 사용 시점 |
|--------|----------|--------|----------|
| Trafilatura | 0.5초 | 높음 | 대부분의 정적 페이지 |
| Newspaper3k | 1초 | 중간 | 표준 뉴스 형식 |
| BeautifulSoup4 | 1초 | 중간 | 한국 언론사 |
| Playwright | 3-5초 | 매우 높음 | 동적 페이지, 마지막 폴백 |

### 최적화 팁

1. **빠른 추출이 필요한 경우**: `use_js=False` 옵션 사용
2. **정확도가 중요한 경우**: 기본 설정 사용 (Playwright 폴백 활성화)
3. **대량 추출 시**: 타임아웃 설정 조정 및 동시성 제한

## API 응답 필드

### methods_tried

추출 과정에서 시도된 모든 추출기 목록을 반환합니다.

```json
{
  "success": true,
  "methods_tried": ["trafilatura", "newspaper", "bs4", "playwright"],
  "data": {...}
}
```

이를 통해 어떤 추출기가 성공했는지, 몇 번의 시도 끝에 성공했는지 확인할 수 있습니다.

## 문제 해결

### 여전히 본문이 제대로 추출되지 않는 경우

1. **타임아웃 증가**: 기본 30초에서 60초로 증가
```python
response = requests.post(
    "http://localhost:8000/api/extract",
    json={"url": "...", "timeout": 60}
)
```

2. **JavaScript 렌더링 강제**: `use_javascript: True` 사용

3. **수동 확인**: `/docs`에서 Swagger UI로 테스트

4. **로그 확인**: 서버 콘솔에서 추출 과정 확인

## 추가 개선 사항

- 추출 실패 시 어떤 추출기가 왜 실패했는지 로그 출력
- 본문 길이 200자 이상 검증으로 짧은 오류 메시지 필터링
- 무효 패턴 자동 감지로 잘못된 추출 방지
