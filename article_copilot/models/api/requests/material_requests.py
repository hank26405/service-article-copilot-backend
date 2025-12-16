"""This file contains the request models for material-related API endpoints."""
from pydantic import BaseModel, Field

class PasteRequest(BaseModel):
    name: str = Field(..., description="素材名稱")
    html_content: str = Field(..., description="從剪貼簿取得的 HTML 內容")