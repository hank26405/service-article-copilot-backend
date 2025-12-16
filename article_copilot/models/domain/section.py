"""Section Domain Model - 章節領域模型"""
from typing import List, Optional, ForwardRef
from pydantic import BaseModel, Field
import uuid

from .content_block import ContentBlock

Section = ForwardRef('Section')


class Section(BaseModel):
    """章節領域模型"""
    section_id: str = Field(default_factory=lambda: f"sec-{uuid.uuid4().hex[:8]}")
    title: str = Field(..., description="章節標題")
    level: int = Field(..., description="章節層級")
    content_blocks: List[ContentBlock] = Field(default_factory=list, description="內容區塊")
    subsections: List['Section'] = Field(default_factory=list, description="子章節")
    section_prompt: Optional[str] = Field(default="", description="生成內容所使用的提示詞")
    reference_material_names: List[str] = Field(default=[], description="生成此章節所參考的素材名稱列表")
    fixed: bool = Field(default=False, description="是否為修訂章節")
    
    def find_subsection(self, section_id: str) -> Optional['Section']:
        """遞迴搜尋子章節"""
        for subsection in self.subsections:
            if subsection.section_id == section_id:
                return subsection
            found = subsection.find_subsection(section_id)
            if found:
                return found
        return None
    
    def count_all_subsections(self) -> int:
        """計算所有子章節數量"""
        count = len(self.subsections)
        for subsection in self.subsections:
            count += subsection.count_all_subsections()
        return count


Section.model_rebuild()