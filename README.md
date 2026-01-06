# News Article Extractor

뉴스 기사 추출 프로젝트 모음입니다.

## 📂 프로젝트

### 1. news_article_extractor
본문, 날짜, 이미지, 영상을 추출하는 간단한 API 서비스

- **포트**: 8000
- **추출 방법**: trafilatura → newspaper3k → playwright
- **특징**: 스마트 필터링, 웹 UI 제공

[상세 문서](news_article_extractor/README.md)

### 2. url_text_extractor
순수 텍스트만 추출하는 API 서비스

- **포트**: 8001
- **추출 방법**: Playwright + Readability
- **특징**: 본문 텍스트에 집중, 간단한 구조

[상세 문서](url_text_extractor/README.md)

## 🚀 빠른 시작

### news_article_extractor 실행
```bash
cd news_article_extractor
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host 0.0.0.0 --port 8000
```

### url_text_extractor 실행
```bash
cd url_text_extractor
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 📄 라이선스

MIT License
