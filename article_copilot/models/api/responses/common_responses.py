"""Common API Response Models"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    """標準成功回應"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """標準錯誤回應"""
    error: str
    message: str
    details: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "NotFound",
                "message": "Resource not found",
                "details": "The resource was not found"
            }
        }


class CacheInfoResponse(BaseModel):
    """快取資訊回應"""
    exists: bool = Field(..., description="快取是否存在")
    ttl: int = Field(..., description="剩餘過期時間(秒)")
    key: str = Field(..., description="Redis key")

    class Config:
        json_schema_extra = {
            "example": {
                "exists": True,
                "ttl": 3456,
                "key": "doc:user123:doc-a1b2c3d4"
            }
        }