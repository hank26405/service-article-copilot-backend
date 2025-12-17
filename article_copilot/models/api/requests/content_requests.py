"""Content API Request Models"""
from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field
from article_copilot.models.domain.content_block import ImageContent, ChartContent, TableContent


class AddContentRequest(BaseModel):
    """新增內容請求"""
    content_type: str = Field(..., description="內容類型", pattern="^(paragraph|image|html)$")
    content: str = Field(..., description="內容文字", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "paragraph",
                "content": "這是一段段落文字。"
            }
        }


class UpdateContentRequest(BaseModel):
    """更新內容請求 - 支援修改 ContentBlock 的所有可編輯欄位"""
    content: Optional[str] = Field(None, description="新的內容文字", min_length=1)
    block_prompt: Optional[str] = Field(None, description="生成內容所使用的提示詞")
    reference_material_names: Optional[List[str]] = Field(None, description="生成此區塊所參考的素材名稱列表")
    reference_examples: Optional[List[str]] = Field(None, description="參考範例列表,用於 LLM 生成時的風格參考")
    llm_raw_output: Optional[str] = Field(None, description="LLM 原始生成結果 (未經處理)")
    fixed: Optional[bool] = Field(None, description="是否為修訂內容區塊")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "這是更新後的內容。",
                "block_prompt": "請用專業的語氣撰寫",
                "reference_material_names": ["material1", "material2"],
                "reference_examples": ["example1"],
                "llm_raw_output": "原始 LLM 輸出...",
                "fixed": True
            }
        }
