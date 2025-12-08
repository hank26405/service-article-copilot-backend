"""Query and output models for the API."""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class Query(BaseModel):
    """User query model."""
    input: str
    user_id: str


class Output(BaseModel):
    """API response model."""
    output: str
    metadata: Optional[Dict[str, Any]] = None  # 新增 metadata 欄位

