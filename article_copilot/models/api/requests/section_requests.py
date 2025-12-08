"""Section API Request Models"""
from typing import Optional
from pydantic import BaseModel, Field


class AddSectionRequest(BaseModel):
    """新增章節請求"""
    title: str = Field(..., description="章節標題", min_length=1, max_length=200)
    parent_section_id: Optional[str] = Field(None, description="父章節 ID，若為頂層章節則為 None")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "第一章",
                "parent_section_id": None
            }
        }


class UpdateSectionTitleRequest(BaseModel):
    """更新章節標題請求"""
    new_title: str = Field(..., description="新的章節標題", min_length=1, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "new_title": "第一章 修訂版"
            }
        }