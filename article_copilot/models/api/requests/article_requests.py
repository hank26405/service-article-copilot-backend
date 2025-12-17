"""Article API Request Models"""
from pydantic import BaseModel, Field


class CreateArticleRequest(BaseModel):
    """建立文章請求"""
    title: str = Field(..., description="文章標題", min_length=1, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "我的第一篇文章",
            }
        }


class UpdateArticleTitleRequest(BaseModel):
    """更新文章標題請求"""
    new_title: str = Field(..., description="新的文章標題", min_length=1, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "new_title": "更新後的文章標題"
            }
        }


class UpdatePromptRequest(BaseModel):
    """更新提示詞請求"""
    new_prompt: str = Field(..., description="新的提示詞", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "new_prompt": "請用專業且易懂的方式撰寫這篇文章"
            }
        }


class UpdateArticlePromptRequest(BaseModel):
    """更新文章提示詞請求"""
    article_prompt: str = Field(..., description="新的文章生成提示詞")

    class Config:
        json_schema_extra = {
            "example": {
                "article_prompt": "請用專業且易懂的語氣撰寫技術文章"
            }
        }