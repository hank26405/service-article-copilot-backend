from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import re

class Material(BaseModel):
    """
    素材領域模型 (Material Domain Model)
    實現 Dual-Representation Strategy (Display View vs LLM View)
    """
    material_id: str = Field(default="", description="素材 ID (filename + uuid)")
    user_id: str = Field(..., description="擁有者 ID")
    shared_with_users: List[str] = Field(default_factory=list, description="共享使用者 ID 列表")
    filename: str = Field(..., description="原始檔名")
    mime_type: str = Field(..., description="檔案類型 (MIME)")
    
    # --- 原始檔儲存 (Cold Storage) ---
    gridfs_id: str = Field(..., description="MongoDB GridFS 中的檔案 ID")
    file_size: int = Field(default=0, description="檔案大小 (bytes)")
    
    # --- 前端呈現層 (Display View) ---
    # 依類型不同:
    # - Excel/Word: HTML String
    # - PPT/Images: URL List (['/api/.../view'])
    # - PDF: API URL String
    display_data: Union[str, List[str], Dict[str, Any]] = Field(
        ..., 
        description="前端渲染用的資料 (HTML string, Image URLs)"
    )
    
    # --- LLM 語意層 (Semantic View) ---
    # 純淨的 Markdown 或 Text，包含頁碼標記，無 HTML 雜訊
    llm_context: str = Field(..., description="供 Prompt 使用的完整文本 (Markdown)")
    
    page_count: int = Field(default=1, description="頁數")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "material_id": "mat-12345678",
                "filename": "Q3_Report.pdf",
                "mime_type": "application/pdf",
                "gridfs_id": "60d5ec...",
                "display_data": "/api/materials/mat-12345678/raw",
                "llm_context": "## --- Page 1 ---\nSales Report...",
                "page_count": 5
            }
        }