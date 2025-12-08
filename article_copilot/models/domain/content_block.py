"""Content Block Domain Model - 內容區塊領域模型"""
from typing import Optional, Union
from pydantic import BaseModel, Field
import uuid


class ImageContent(BaseModel):
    """圖片內容"""
    path: str = Field(..., description="圖片路徑")
    caption: str = Field(default="", description="圖片說明")


class ChartContent(BaseModel):
    """圖表內容"""
    chart_type: str = Field(..., description="圖表類型")
    data: dict = Field(..., description="圖表資料")
    title: str = Field(default="", description="圖表標題")


class ContentBlock(BaseModel):
    """內容區塊領域模型"""
    block_id: str = Field(default_factory=lambda: f"blk-{uuid.uuid4().hex[:8]}")
    type: str = Field(..., description="內容類型: paragraph, image, chart, html")
    content: Union[str, ImageContent, ChartContent] = Field(..., description="內容資料")
    block_prompt: Optional[str] = Field(default="", description="生成內容所使用的提示詞")
    fixed: bool = Field(default=False, description="是否為修訂內容區塊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "block_id": "blk-x1y2z3w4",
                "type": "paragraph",
                "content": "這是一段文字內容",
                "block_prompt": "",
                "fixed": False
            }
        }