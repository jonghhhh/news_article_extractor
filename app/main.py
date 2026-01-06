"""
News Article Extractor API
FastAPI-based web service for extracting article data from URLs
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from typing import List, Optional
import json
import os
from datetime import datetime
from pathlib import Path

from .models import ArticleData, ExtractionRequest, ExtractionResponse
from .extractors import ArticleExtractor


# Initialize FastAPI app
app = FastAPI(
    title="News Article Extractor",
    description="""
    뉴스 기사 URL에서 제목, 본문, 날짜, 기자, 이미지, 영상 등 
    다양한 정보를 자동으로 추출하는 API 서비스
    
    ## 특징
    - 다중 추출 엔진 (Trafilatura, Newspaper3k, BeautifulSoup, Playwright)
    - 자동 폴백 메커니즘 (하나 실패 시 다음 방법으로 자동 전환)
    - 한국 주요 언론사 최적화 패턴
    - 영상 URL 추출 (방송사 기사)
    - JSON flat key 구조 출력
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize extractor
extractor = ArticleExtractor(use_playwright=False)

# Storage directory for saved results
STORAGE_DIR = Path("./data")
STORAGE_DIR.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    static_path = Path(__file__).parent.parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(static_path)
    return HTMLResponse("""
    <html>
        <head><title>News Extractor API</title></head>
        <body>
            <h1>News Article Extractor API</h1>
            <p>Visit <a href="/docs">/docs</a> for API documentation</p>
        </body>
    </html>
    """)


@app.get("/api/extract", response_model=ExtractionResponse)
async def extract_article(
    url: str = Query(..., description="추출할 기사 URL"),
    timeout: int = Query(30, ge=5, le=120, description="타임아웃 (초)"),
    use_js: bool = Query(False, description="JavaScript 렌더링 사용 (느림)")
):
    """
    GET 방식으로 기사 추출
    
    - **url**: 추출할 뉴스 기사 URL
    - **timeout**: 요청 타임아웃 (기본 30초)
    - **use_js**: JavaScript 렌더링 사용 여부 (Playwright 사용, 느림)
    """
    try:
        # Create extractor with or without Playwright
        ext = ArticleExtractor(use_playwright=use_js)
        result = await ext.extract(url, timeout)
        
        if result["success"]:
            return ExtractionResponse(
                success=True,
                data=ArticleData(**result["data"]),
                methods_tried=result["methods_tried"]
            )
        else:
            return ExtractionResponse(
                success=False,
                error=result["error"],
                methods_tried=result["methods_tried"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract_article_post(request: ExtractionRequest):
    """
    POST 방식으로 기사 추출
    
    Request Body:
    - **url**: 추출할 뉴스 기사 URL
    - **timeout**: 요청 타임아웃 (기본 30초)
    - **use_javascript**: JavaScript 렌더링 사용 여부
    """
    try:
        ext = ArticleExtractor(use_playwright=request.use_javascript)
        result = await ext.extract(request.url, request.timeout)
        
        if result["success"]:
            return ExtractionResponse(
                success=True,
                data=ArticleData(**result["data"]),
                methods_tried=result["methods_tried"]
            )
        else:
            return ExtractionResponse(
                success=False,
                error=result["error"],
                methods_tried=result["methods_tried"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract/batch")
async def extract_batch(
    urls: List[str],
    timeout: int = Query(30, ge=5, le=120),
    concurrency: int = Query(5, ge=1, le=10)
):
    """
    여러 URL 일괄 추출
    
    - **urls**: 추출할 URL 목록
    - **timeout**: URL당 타임아웃
    - **concurrency**: 동시 처리 수
    """
    try:
        results = await extractor.extract_multiple(urls, timeout, concurrency)
        
        return {
            "total": len(urls),
            "success_count": sum(1 for r in results if r["success"]),
            "failed_count": sum(1 for r in results if not r["success"]),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract/save")
async def extract_and_save(
    url: str = Query(..., description="추출할 기사 URL"),
    filename: Optional[str] = Query(None, description="저장할 파일명 (확장자 제외)")
):
    """
    기사 추출 후 JSON 파일로 저장
    
    - **url**: 추출할 기사 URL
    - **filename**: 저장할 파일명 (미지정시 타임스탬프 사용)
    """
    try:
        result = await extractor.extract(url)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"article_{timestamp}"
        
        filepath = STORAGE_DIR / f"{filename}.json"
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result["data"], f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"Saved to {filepath}",
            "data": result["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/saved")
async def list_saved():
    """저장된 JSON 파일 목록"""
    files = list(STORAGE_DIR.glob("*.json"))
    return {
        "count": len(files),
        "files": [f.name for f in files]
    }


@app.get("/api/saved/{filename}")
async def get_saved(filename: str):
    """저장된 JSON 파일 조회"""
    filepath = STORAGE_DIR / filename
    if not filepath.suffix:
        filepath = filepath.with_suffix(".json")
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


@app.get("/api/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "extractors": [e.name for e in extractor.extractors]
    }


# Mount static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
