"""This file contains the request models for material-related API endpoints."""
from typing import Optional
from pydantic import BaseModel, Field

class PasteRequest(BaseModel):
    filename: Optional[str] = Field(None, description="素材名稱")
    html_content: str = Field(..., description="從剪貼簿取得的 HTML 內容")