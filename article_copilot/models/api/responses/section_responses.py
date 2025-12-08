"""Section API Response Models"""
from pydantic import BaseModel, Field


class AddSectionResponse(BaseModel):
    """新增章節回應"""
    section_id: str = Field(..., description="新建章節的 ID")
    message: str = Field(..., description="操作訊息")

    class Config:
        json_schema_extra = {
            "example": {
                "section_id": "sec-x1y2z3w4",
                "message": "Section created successfully"
            }
        }