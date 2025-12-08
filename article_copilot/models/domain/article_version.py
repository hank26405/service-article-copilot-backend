"""Article Version Model - 文章版本模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ArticleVersion(BaseModel):
    """文章版本紀錄"""
    version_id: str = Field(default_factory=lambda: f"ver-{uuid.uuid4().hex[:8]}")
    article_id: str
    user_id: str
    version_number: int  # 版本號 (1, 2, 3...)
    snapshot: dict  # 文章完整快照 (Article.model_dump())
    operation: str  # 操作類型 (create, add_section, update_paragraph, etc.)
    operation_desc: str  # 操作描述
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}