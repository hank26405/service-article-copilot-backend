"""Authentication Response Models"""
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Token 回應"""
    access_token: str = Field(..., description="JWT Access Token")
    token_type: str = Field(default="bearer", description="Token 類型")
    expires_in: int = Field(..., description="Token 有效時間 (秒)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 43200
                }
            ]
        }
    }