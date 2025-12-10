"""Authentication Request Models"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登入請求"""
    email_address: EmailStr = Field(..., description="使用者 Email")
    password: str = Field(..., min_length=8, description="使用者密碼")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email_address": "user@example.com",
                    "password": "***"
                }
            ]
        }
    }