"""Content API Request Models"""
from pydantic import BaseModel, Field


class AddContentRequest(BaseModel):
    """新增內容請求"""
    section_id: str = Field(..., description="章節 ID")
    content_type: str = Field(..., description="內容類型", pattern="^(paragraph|html)$")
    content: str = Field(..., description="內容文字", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "section_id": "sec-x1y2z3w4",
                "content_type": "paragraph",
                "content": "這是一段段落文字。"
            }
        }


class UpdateContentRequest(BaseModel):
    """更新內容請求"""
    content: str = Field(..., description="新的內容文字", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "這是更新後的內容。"
            }
        }