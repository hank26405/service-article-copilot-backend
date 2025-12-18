"""This file contains the request models for material-related API endpoints."""
from typing import Optional
from pydantic import BaseModel, Field

class PasteRequest(BaseModel):
    html_content: str
    filename: Optional[str] = None

class TextUploadRequest(BaseModel):
    text_content: str
    filename: Optional[str] = None
    content_type: str = "text/plain"  # 可以是 "text/plain" 或 "application/json"