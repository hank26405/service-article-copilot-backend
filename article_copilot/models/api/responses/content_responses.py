"""Content API Response Models"""
from pydantic import BaseModel, Field


class AddContentResponse(BaseModel):
    """新增內容回應"""
    block_id: str = Field(..., description="新建內容區塊的 ID")
    message: str = Field(..., description="操作訊息")

    class Config:
        json_schema_extra = {
            "example": {
                "block_id": "blk-p1q2r3s4",
                "message": "Content added successfully"
            }
        }