"""Content Block Domain Model - 內容區塊領域模型 (Updated)"""
from typing import Optional, Union, List, Any
from pydantic import BaseModel, Field
import uuid


class ImageContent(BaseModel):
    """圖片內容"""
    path: str = Field(..., description="圖片路徑 (或 API URL)")
    caption: str = Field(default="", description="圖片說明")


class ChartContent(BaseModel):
    """圖表內容"""
    chart_type: str = Field(..., description="圖表類型")
    data: dict = Field(..., description="圖表資料")
    title: str = Field(default="", description="圖表標題")


class TableContent(BaseModel):
    """表格內容 (New) - 用於儲存從 Excel 貼上或 CSV 匯入的結構化數據"""
    headers: List[str] = Field(default=[], description="表頭欄位名稱")
    rows: List[List[Any]] = Field(..., description="表格資料列 (二維陣列)")
    caption: str = Field(default="", description="表格標題/說明")



class ContentBlock(BaseModel):
    """內容區塊領域模型"""
    block_id: str = Field(default_factory=lambda: f"blk-{uuid.uuid4().hex[:8]}")
    type: str = Field(..., description="內容類型: paragraph, image, chart, html, table, file")
    content: Union[str, ImageContent, ChartContent, TableContent] = Field(..., description="內容資料")
    block_prompt: Optional[str] = Field(default="", description="生成內容所使用的提示詞")
    reference_material_names: List[str] = Field(default=[], description="生成此區塊所參考的素材名稱列表")
    fixed: bool = Field(default=False, description="是否為修訂內容區塊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "block_id": "blk-x1y2z3w4",
                "type": "paragraph",
                "content": "這是一段文字內容",
                "block_prompt": "",
                "reference_material_names": ["material1", "material2"],
                "fixed": False
            }
        }