from typing import Optional
from pydantic import BaseModel


class UserResponse(BaseModel):
    """使用者回應(不包含密碼)"""
    id: str
    email_address: str
    authority: str
    name: Optional[str] = None
    additional_info: Optional[str] = None  # 用於返回預設密碼等額外資訊
