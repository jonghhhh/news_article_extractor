# main.py - 간단한 뉴스 기사 추출 API

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from extractor import ArticleExtractor

app = FastAPI(
    title="News Article Extractor",
    description="뉴스 기사의 본문, 날짜, 이미지, 영상을 추출합니다",
    version="2.0.0"
)


class ExtractRequest(BaseModel):
    url: str


class ExtractResponse(BaseModel):
    url: str
    title: str
    text: str
    date: str
    images: List[str]
    videos: List[str]
    method: str


@app.get("/", response_class=HTMLResponse)
def read_root():
    """API 사용 페이지"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>News Article Extractor API</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .status {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
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
        .endpoints {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 News Article Extractor</h1>
        <div class="status">✓ API 작동 중</div>

        <h2>URL 입력</h2>
        <input type="text" id="urlInput" placeholder="https://news.example.com/article/123"
               value="https://n.news.naver.com/article/422/0000819667">
        <button onclick="extractArticle()">추출하기</button>

        <div id="result"></div>

        <div class="endpoints">
            <h3>API 엔드포인트</h3>
            <p><span class="method-tag">POST</span> <code>/extract</code> - JSON으로 URL 전송</p>
            <p><span class="method-tag">GET</span> <code>/extract?url=...</code> - 쿼리 파라미터로 URL 전송</p>
            <p><span class="method-tag">GET</span> <code>/docs</code> - Swagger UI</p>
        </div>

        <h3>추출 정보</h3>
        <ul>
            <li>제목 (title)</li>
            <li>본문 텍스트 (text)</li>
            <li>날짜 (date)</li>
            <li>이미지 URL (images)</li>
            <li>영상 URL (videos)</li>
            <li>사용된 추출 방법 (method: trafilatura → newspaper3k → playwright)</li>
        </ul>
    </div>

    <script>
        async function extractArticle() {
            const url = document.getElementById('urlInput').value;
            const resultDiv = document.getElementById('result');

            if (!url) {
                resultDiv.innerHTML = '<div class="result error">URL을 입력하세요</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="result">⏳ 추출 중...</div>';

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
                            <div>${data.images.join('<br>') || '없음'}</div>

                            <div class="label">영상 (${data.videos.length}개):</div>
                            <div>${data.videos.join('<br>') || '없음'}</div>
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


@app.post("/extract", response_model=ExtractResponse)
async def extract_post(req: ExtractRequest):
    """POST 방식 추출"""
    try:
        result = await ArticleExtractor.extract(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/extract", response_model=ExtractResponse)
async def extract_get(url: str):
    """GET 방식 추출"""
    try:
        result = await ArticleExtractor.extract(url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
