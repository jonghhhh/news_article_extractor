# main.py - 간단한 뉴스 기사 추출 API

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from extractor import ArticleExtractor

app = FastAPI(
    title="News Article Extractor",
    description="뉴스 기사의 본문, 날짜, 이미지를 추출합니다 (v2.2.0: 60-70% 속도 향상, 정확도 대폭 개선)",
    version="2.2.0"
)


class ExtractRequest(BaseModel):
    url: str


class ExtractResponse(BaseModel):
    url: str
    title: str
    text: str
    date: str
    images: List[str]
    method: str


@app.get("/", response_class=HTMLResponse)
def read_root():
    """API 사용 페이지"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Article Extractor API</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #444;
            margin-top: 30px;
        }
        h3 {
            color: #555;
            margin-top: 20px;
        }
        .status {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            margin: 20px 0;
        }
        .warning {
            background: #ff9800;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .info {
            background: #2196F3;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 30px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 5px;
            white-space: pre-wrap;
            max-height: 500px;
            overflow-y: auto;
        }
        .error {
            border-left-color: #f44336;
            background: #ffebee;
        }
        .label {
            font-weight: bold;
            color: #555;
            margin-top: 15px;
            display: block;
        }
        .code-block {
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        code {
            background: #263238;
            color: #aed581;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .method-tag {
            background: #2196F3;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        ul {
            margin: 10px 0;
            padding-left: 25px;
        }
        li {
            margin: 5px 0;
        }
        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom: 3px solid #4CAF50;
            font-weight: bold;
            color: #4CAF50;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .tab-title {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .tab-icon {
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 News Article Extractor API</h1>
        <div class="status">✓ API 작동 중 (Render Starter - 512MB RAM)</div>

        <h2>🧪 빠른 테스트</h2>
        <input type="text" id="urlInput" placeholder="https://news.example.com/article/123"
               value="https://n.news.naver.com/article/422/0000819667">
        <button onclick="extractArticle()">추출하기</button>

        <div id="result"></div>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('usage')">
                <span class="tab-title"><span class="tab-icon">📖</span> API 사용법</span>
            </button>
            <button class="tab" onclick="showTab('python')">
                <span class="tab-title"><span class="tab-icon">🐍</span> Python 코드</span>
            </button>
            <button class="tab" onclick="showTab('limits')">
                <span class="tab-title"><span class="tab-icon">⚠️</span> 제약사항</span>
            </button>
            <button class="tab" onclick="showTab('api')">
                <span class="tab-title"><span class="tab-icon">🔌</span> API 문서</span>
            </button>
        </div>

        <div id="usage" class="tab-content active">
            <h2>📖 API 사용 방법</h2>

            <h3>1️⃣ POST 방식 (추천)</h3>
            <div class="code-block">curl -X POST https://news-article-extractor.onrender.com/extract \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://n.news.naver.com/article/422/0000819667"}'</div>

            <h3>2️⃣ GET 방식</h3>
            <div class="code-block">curl "https://news-article-extractor.onrender.com/extract?url=https://n.news.naver.com/article/422/0000819667"</div>

            <h3>3️⃣ 응답 형식</h3>
            <div class="code-block">{
  "url": "https://...",
  "title": "기사 제목",
  "text": "본문 내용...",
  "date": "2026-01-06",
  "images": ["https://...", "https://..."],
  "method": "trafilatura"
}</div>

            <h3>📊 추출 정보</h3>
            <table>
                <tr>
                    <th>필드</th>
                    <th>설명</th>
                </tr>
                <tr>
                    <td><code>title</code></td>
                    <td>기사 제목</td>
                </tr>
                <tr>
                    <td><code>text</code></td>
                    <td>본문 텍스트 (광고/저작권 문구 제거됨)</td>
                </tr>
                <tr>
                    <td><code>date</code></td>
                    <td>발행일 (YYYY-MM-DD)</td>
                </tr>
                <tr>
                    <td><code>images</code></td>
                    <td>이미지 URL 목록 (최대 5개, 로고/배너/GIF 제외)</td>
                </tr>
                <tr>
                    <td><code>method</code></td>
                    <td>사용된 추출 방법 (trafilatura, newspaper3k, playwright)</td>
                </tr>
            </table>
        </div>

        <div id="python" class="tab-content">
            <h2>🐍 Python에서 사용하기</h2>

            <h3>1️⃣ requests 라이브러리 사용</h3>
            <div class="code-block">import requests

# 단일 기사 추출
url = "https://n.news.naver.com/article/422/0000819667"

response = requests.post(
    "https://news-article-extractor.onrender.com/extract",
    json={"url": url}
)

data = response.json()
print(f"제목: {data['title']}")
print(f"본문: {data['text'][:200]}...")  # 처음 200자만
print(f"날짜: {data['date']}")
print(f"방법: {data['method']}")</div>

            <h3>2️⃣ 여러 기사 처리 (순차)</h3>
            <div class="code-block">import requests
import time
import json

urls = [
    "https://n.news.naver.com/article/001/0000001",
    "https://n.news.naver.com/article/001/0000002",
    # ... 더 많은 URL
]

results = []

for url in urls:
    try:
        response = requests.post(
            "https://news-article-extractor.onrender.com/extract",
            json={"url": url},
            timeout=30  # 30초 타임아웃
        )

        if response.status_code == 200:
            data = response.json()
            results.append(data)
            print(f"✓ {data['title'][:50]}")
        else:
            print(f"✗ 실패: {url}")

    except Exception as e:
        print(f"✗ 에러: {url} - {e}")

    time.sleep(2)  # Rate limiting (중요!)

# 결과 저장
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)</div>

            <h3>3️⃣ aiohttp로 병렬 처리 (빠름)</h3>
            <div class="code-block">import aiohttp
import asyncio
import json

async def extract_article(session, url):
    # 단일 기사 추출
    try:
        async with session.post(
            "https://news-article-extractor.onrender.com/extract",
            json={"url": url},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            return await response.json()
    except Exception as e:
        return {"error": str(e), "url": url}

async def extract_multiple(urls, batch_size=3):
    # 여러 기사를 배치로 처리
    async with aiohttp.ClientSession() as session:
        results = []

        # 3개씩 묶어서 처리
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            tasks = [extract_article(session, url) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Rate limiting
            if i + batch_size < len(urls):
                await asyncio.sleep(2)

        return results

# 실행
urls = ["https://...", "https://...", ...]
results = asyncio.run(extract_multiple(urls))

# 저장
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)</div>

            <h3>4️⃣ pandas로 CSV 저장</h3>
            <div class="code-block">import pandas as pd
import requests

urls = [...]  # URL 목록
results = []

for url in urls:
    response = requests.post(
        "https://news-article-extractor.onrender.com/extract",
        json={"url": url}
    )
    if response.status_code == 200:
        results.append(response.json())

# DataFrame 생성
df = pd.DataFrame(results)

# CSV 저장
df.to_csv("articles.csv", index=False, encoding="utf-8-sig")

print(f"총 {len(df)}개 기사 저장 완료")</div>
        </div>

        <div id="limits" class="tab-content">
            <h2>⚠️ 서비스 제약사항</h2>

            <div class="warning">
                <strong>⚠️ 현재 Render Starter Plan (512MB RAM, 0.5 CPU) 사용 중</strong>
            </div>

            <h3>🐌 성능 제약</h3>
            <table>
                <tr>
                    <th>항목</th>
                    <th>제약</th>
                    <th>설명</th>
                </tr>
                <tr>
                    <td>메모리</td>
                    <td>512MB</td>
                    <td>Playwright 실행 시 메모리 부족 가능</td>
                </tr>
                <tr>
                    <td>CPU</td>
                    <td>0.5 코어</td>
                    <td>JavaScript 렌더링이 느릴 수 있음</td>
                </tr>
                <tr>
                    <td>동시 처리</td>
                    <td>1개</td>
                    <td>순차 처리만 가능</td>
                </tr>
                <tr>
                    <td>요청 타임아웃</td>
                    <td>20초</td>
                    <td>복잡한 페이지는 실패 가능</td>
                </tr>
            </table>

            <h3>⏱️ 처리 시간</h3>
            <ul>
                <li><strong>trafilatura 성공</strong>: 2-3초 (빠름) ✅</li>
                <li><strong>newspaper3k 성공</strong>: 3-5초 (보통) ✅</li>
                <li><strong>playwright 필요</strong>: 15-25초 (느림) ⚠️</li>
            </ul>

            <h3>📰 지원 사이트</h3>
            <table>
                <tr>
                    <th>사이트</th>
                    <th>상태</th>
                    <th>방법</th>
                </tr>
                <tr>
                    <td>네이버 뉴스</td>
                    <td>✅ 빠름</td>
                    <td>trafilatura</td>
                </tr>
                <tr>
                    <td>SBS 뉴스</td>
                    <td>✅ 빠름</td>
                    <td>trafilatura</td>
                </tr>
                <tr>
                    <td>조선일보</td>
                    <td>⚠️ 느림</td>
                    <td>playwright (20초)</td>
                </tr>
                <tr>
                    <td>해외 언론</td>
                    <td>❌ 불안정</td>
                    <td>playwright (타임아웃 가능)</td>
                </tr>
            </table>

            <h3>🚫 대량 처리 제약</h3>
            <div class="info">
                <strong>대량 기사 처리 시 주의사항:</strong><br>
                • Render 무료/저가 플랜에서는 처리 속도 제한이 있습니다<br>
                • Rate limiting 필수 (2초 간격 권장)<br>
                • IP 차단 위험 있음<br>
                <br>
                <strong>권장:</strong> 로컬에서 Docker로 실행 시 훨씬 빠른 처리 가능
            </div>

            <h3>💡 대량 처리 방법</h3>
            <ol>
                <li><strong>로컬 Docker 사용</strong> (가장 빠름)
                    <div class="code-block">docker-compose up
# 로컬 http://localhost:10000 사용</div>
                </li>
                <li><strong>배치 크기 제한</strong>: 한 번에 10-50개씩만 처리</li>
                <li><strong>Rate limiting</strong>: 요청 간 2초 대기</li>
                <li><strong>재시도 로직</strong>: 실패 시 3번까지 재시도</li>
            </ol>

            <h3>📦 소스코드</h3>
            <div class="info">
                <strong>GitHub Repository:</strong><br>
                <a href="https://github.com/jonghhhh/news_article_extractor" target="_blank" style="color: #ffffff; text-decoration: underline;">
                    https://github.com/jonghhhh/news_article_extractor
                </a>
                <br><br>
                • 전체 소스코드 및 Docker 설정 파일 확인 가능<br>
                • 로컬 실행 방법 및 상세 문서 포함<br>
                • Issues/PR 환영합니다
            </div>
        </div>

        <div id="api" class="tab-content">
            <h2>🔌 API 엔드포인트</h2>

            <h3><span class="method-tag">POST</span> /extract</h3>
            <p><strong>Request:</strong></p>
            <div class="code-block">{
  "url": "https://news.example.com/article/123"
}</div>

            <p><strong>Response (200 OK):</strong></p>
            <div class="code-block">{
  "url": "https://...",
  "title": "기사 제목",
  "text": "본문...",
  "date": "2026-01-06",
  "images": [...],
  "method": "trafilatura"
}</div>

            <p><strong>Response (500 Error):</strong></p>
            <div class="code-block">{
  "detail": "모든 추출 방법 실패: 본문을 찾을 수 없습니다"
}</div>

            <h3><span class="method-tag">GET</span> /extract?url=...</h3>
            <p>쿼리 파라미터로 URL 전달</p>
            <div class="code-block">GET /extract?url=https%3A%2F%2Fnews.example.com%2Farticle%2F123</div>

            <h3><span class="method-tag">GET</span> /docs</h3>
            <p>Swagger UI 문서: <a href="/docs" target="_blank">https://news-article-extractor.onrender.com/docs</a></p>

            <h3>📊 추출 방법 우선순위</h3>
            <ol>
                <li><strong>trafilatura</strong>: 빠르고 정확 (대부분의 뉴스 사이트)</li>
                <li><strong>newspaper3k</strong>: trafilatura 실패 시 (한국어 최적화)</li>
                <li><strong>playwright</strong>: JavaScript 렌더링 필요 시 (느림)</li>
            </ol>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // 모든 탭 비활성화
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // 선택한 탭 활성화
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }

        async function extractArticle() {
            const url = document.getElementById('urlInput').value;
            const resultDiv = document.getElementById('result');

            if (!url) {
                resultDiv.innerHTML = '<div class="result error">URL을 입력하세요</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="result">⏳ 추출 중... (최대 25초 소요 가능)</div>';

            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = `
                        <div class="result">
                            <div class="label">✓ 추출 성공 (방법: ${data.method})</div>

                            <div class="label">제목:</div>
                            <div>${data.title || '없음'}</div>

                            <div class="label">날짜:</div>
                            <div>${data.date || '없음'}</div>

                            <div class="label">본문 (${data.text.length}자):</div>
                            <div style="white-space: pre-wrap;">${data.text}</div>

                            <div class="label">이미지 (${data.images.length}개):</div>
                            <div>${data.images.slice(0, 3).join('<br>') || '없음'}${data.images.length > 3 ? '<br>...' : ''}</div>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="result error">❌ 오류: ${data.detail}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error">❌ 네트워크 오류: ${error.message}</div>`;
            }
        }

        // Enter 키로 실행
        document.getElementById('urlInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') extractArticle();
        });
    </script>
</body>
</html>
    """


@app.post("/extract")
def extract_post(req: ExtractRequest):
    """POST 방식 추출"""
    try:
        result = ArticleExtractor.extract(req.url)
        import json
        return JSONResponse(
            content=json.loads(json.dumps(result, ensure_ascii=False)),
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/extract")
def extract_get(url: str):
    """GET 방식 추출"""
    try:
        result = ArticleExtractor.extract(url)
        import json
        return JSONResponse(
            content=json.loads(json.dumps(result, ensure_ascii=False)),
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
