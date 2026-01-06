"""
Pydantic models for news article extraction
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ArticleData(BaseModel):
    """Extracted article data model with flat JSON structure"""
    
    # 기본 정보
    url: str = Field(..., description="원본 기사 URL")
    title: Optional[str] = Field(None, description="기사 제목")
    content: Optional[str] = Field(None, description="기사 본문")
    summary: Optional[str] = Field(None, description="기사 요약")
    
    # 메타 정보
    published_date: Optional[str] = Field(None, description="발행일")
    modified_date: Optional[str] = Field(None, description="수정일")
    author: Optional[str] = Field(None, description="기자/작성자")
    authors: Optional[List[str]] = Field(None, description="기자/작성자 목록")
    
    # 미디어
    main_image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    image_urls: Optional[List[str]] = Field(None, description="본문 이미지 URL 목록")
    video_url: Optional[str] = Field(None, description="영상 URL (방송 기사)")
    video_urls: Optional[List[str]] = Field(None, description="영상 URL 목록")
    
    # 분류 정보
    category: Optional[str] = Field(None, description="카테고리/섹션")
    tags: Optional[List[str]] = Field(None, description="태그/키워드")
    keywords: Optional[List[str]] = Field(None, description="키워드")
    
    # 통계 정보
    view_count: Optional[int] = Field(None, description="조회수")
    like_count: Optional[int] = Field(None, description="좋아요 수")
    comment_count: Optional[int] = Field(None, description="댓글 수")
    share_count: Optional[int] = Field(None, description="공유 수")
    
    # 언론사 정보
    source_name: Optional[str] = Field(None, description="언론사명")
    source_domain: Optional[str] = Field(None, description="언론사 도메인")
    
    # 메타데이터
    language: Optional[str] = Field(None, description="언어")
    extraction_method: Optional[str] = Field(None, description="추출에 사용된 방법")
    extraction_time: Optional[str] = Field(None, description="추출 시간")
    
    # Open Graph / Twitter Card
    og_title: Optional[str] = Field(None, description="OG 제목")
    og_description: Optional[str] = Field(None, description="OG 설명")
    og_image: Optional[str] = Field(None, description="OG 이미지")
    og_type: Optional[str] = Field(None, description="OG 타입")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/news/12345",
                "title": "기사 제목 예시",
                "content": "기사 본문 내용...",
                "published_date": "2024-01-15T10:30:00",
                "author": "홍길동 기자",
                "main_image_url": "https://example.com/images/news.jpg",
                "category": "정치",
                "view_count": 1234,
                "source_name": "예시뉴스",
                "extraction_method": "trafilatura"
            }
        }


class ExtractionRequest(BaseModel):
    """Request model for article extraction"""
    url: str = Field(..., description="추출할 기사 URL")
    timeout: Optional[int] = Field(30, description="타임아웃 (초)")
    use_javascript: Optional[bool] = Field(False, description="JavaScript 렌더링 사용 여부")


class ExtractionResponse(BaseModel):
    """Response model for extraction result"""
    success: bool
    data: Optional[ArticleData] = None
    error: Optional[str] = None
    methods_tried: List[str] = Field(default_factory=list)
