from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Login request"""
    email_address: str
    password: str