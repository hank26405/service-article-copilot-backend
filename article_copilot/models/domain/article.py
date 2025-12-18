"""Article Domain Model - 文章領域模型"""
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from .section import Section


class Article(BaseModel):
    """文章領域模型 - 代表系統中的文章實體"""
    article_id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4().hex[:8]}")
    user_id: str = Field(..., description="文章所有者的使用者 ID")
    title: str = Field(..., description="文章標題")
    sections: List[Section] = Field(default_factory=list, description="文章的章節列表")
    metadata: dict = Field(default_factory=dict, description="文章元數據")
    article_prompt: Optional[str] = Field(default="", description="生成內容所使用的提示詞")
    reference_material_ids: List[str] = Field(default=[], description="整篇文章的通用參考素材名稱列表 (全域 Context)")
    fixed: bool = Field(default=False, description="是否為修訂文章")
    
    def find_section(self, section_id: str) -> Optional[Section]:
        """遞迴搜尋章節"""
        for section in self.sections:
            if section.section_id == section_id:
                return section
            found = section.find_subsection(section_id)
            if found:
                return found
        return None
    
    def get_section_count(self) -> int:
        """取得總章節數 (包含子章節)"""
        count = len(self.sections)
        for section in self.sections:
            count += section.count_all_subsections()
        return count

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "doc-a1b2c3d4",
                "user_id": "user123",
                "title": "我的第一篇文章",
                "sections": [],
                "metadata": {},
                "article_prompt": "",
                "reference_material_ids": [],
            }
        }
