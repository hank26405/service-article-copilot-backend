from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TokenData(BaseModel):
    """JWT Token payload data"""
    sub: str  # subject (email_address)
    scopes: List[str]
    user_id: str
    iat: datetime  # issued at
    exp: datetime  # expiration time


class Token(BaseModel):
    """Access token response"""
    access_token: str
    token_type: str = "bearer"
