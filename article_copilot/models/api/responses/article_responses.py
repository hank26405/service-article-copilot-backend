"""Article API Response Models"""
from typing import List
from article_copilot.models.domain.section import Section
from pydantic import BaseModel, Field


class CreateArticleResponse(BaseModel):
    """建立文章回應"""
    article_id: str = Field(..., description="新建文章的 ID")
    message: str = Field(default="Article created successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "doc-a1b2c3d4",
                "message": "Article created successfully"
            }
        }


class ArticleSummary(BaseModel):
    """文章摘要"""
    article_id: str = Field(..., description="文章 ID")
    user_id: str = Field(..., description="使用者 ID")
    title: str = Field(..., description="文章標題")
    section_count: int = Field(..., description="章節數量")

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "doc-a1b2c3d4",
                "user_id": "user123",
                "title": "我的第一篇文章",
                "section_count": 3
            }
        }


class ArticlesTitleResponse(BaseModel):
    """文章列表回應"""
    articles_id: str = Field(..., description="文章 ID")
    title: str = Field(..., description="文章標題")


class ArticleStructureResponse(BaseModel):
    """文章結構回應"""
    article_id: str = Field(..., description="文章 ID")
    article_title: str = Field(..., description="文章標題")
    user_id: str = Field(..., description="使用者 ID")
    total_sections: int = Field(..., description="頂層章節總數")
    sections: List[Section] = Field(..., description="章節結構列表")

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "doc-a1b2c3d4",
                "article_title": "我的第一篇文章",
                "user_id": "user123",
                "total_sections": 2,
                "sections": [
                    {
                        "section_id": "sec-xyz789",
                        "title": "第一章",
                        "level": 1,
                        "content_blocks": [],
                        "subsections": []
                    }
                ]
            }
        }