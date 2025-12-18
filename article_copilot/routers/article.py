"""Article CRUD Router - 文章基本操作 API"""
from typing import List
from article_copilot.models.api.requests.article_requests import UpdateArticleTitleRequest, UpdateArticlePromptRequest
from fastapi import APIRouter, HTTPException, Path, Body, Depends

from article_copilot.configs.logger_setting import log
from article_copilot.models.domain.user import User
from article_copilot.security.auth import get_current_user

from article_copilot.services.article_manager import (
    create_new_article,
    export_article_as_json,
    list_my_articles,
    add_main_section,
    add_subsection,
    add_content_block,
    replace_section,
    update_article_prompt,
    update_article_title,
    delete_section,
    delete_content_block,
    delete_article,
    copy_article_to_user,
    ArticleManager
)

from article_copilot.exceptions import (
    ArticleNotFoundError,
    SectionNotFoundError,
    ContentBlockNotFoundError,
    DatabaseConnectionError,
    InvalidContentTypeError,
    ValidationError,
)

from article_copilot.models import (
    CreateArticleRequest,
    AddSectionRequest,
    AddContentRequest,
    UpdateArticleTitleRequest,
    CreateArticleResponse,
    ArticlesTitleResponse,
    AddSectionResponse,
    AddContentResponse,
    StandardResponse,
)

from article_copilot.models.api.responses.article_responses import ArticleStructureResponse
from article_copilot.models.domain.section import Section


def create_article_router() -> APIRouter:
    """建立文章管理 Router"""
    
    router = APIRouter()
    
    # ==================== 文章 CRUD ====================

    @router.post("/", response_model=CreateArticleResponse)
    async def create_article(
        request: CreateArticleRequest,
        current_user: User = Depends(get_current_user)
    ):
        """建立新文章"""
        try:
            article_id = create_new_article(current_user.id, request.title)
            return CreateArticleResponse(
                article_id=article_id,
                message="Article created successfully"
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            raise HTTPException(status_code=503, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.get("/", response_model=List[ArticlesTitleResponse])
    async def get_articles(current_user: User = Depends(get_current_user)):
        """取得使用者的文章列表"""
        try:
            return list_my_articles(current_user.id)
        except Exception as e:
            log.error(f"Error listing articles: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.get("/{article_id}/json", response_model=dict)
    async def export_article(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """匯出文章為 JSON"""
        try:
            result = export_article_as_json(current_user.id, article_id)
            import json
            return json.loads(result)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Export error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.delete("/{article_id}", response_model=StandardResponse)
    async def remove_article(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """刪除文章"""
        try:
            result = delete_article(current_user.id, article_id)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Delete error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    # ==================== 章節管理 ====================

    @router.post("/{article_id}/sections", response_model=AddSectionResponse)
    async def create_section(
        article_id: str = Path(...),
        request: AddSectionRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """新增章節"""
        try:
            if request.parent_section_id:
                section_id, result = add_subsection(current_user.id, article_id, request.parent_section_id, request.title)
            else:
                section_id, result = add_main_section(current_user.id, article_id, request.title)
            return AddSectionResponse(section_id=section_id, message=result)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.post("/{article_id}/sections/{section_id}/subsections", response_model=AddSectionResponse)
    async def create_subsection(
        article_id: str = Path(...),
        section_id: str = Path(..., description="父章節 ID"),
        request: AddSectionRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """在指定章節下新增子章節"""
        try:
            subsection_id, result = add_subsection(
                current_user.id, 
                article_id, 
                section_id, 
                request.title
            )
            return AddSectionResponse(section_id=subsection_id, message=result)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.patch("/{article_id}/sections/", response_model=StandardResponse)
    async def update_section(
        article_id: str = Path(...),
        request: Section = Body(..., description="更新後的完整章節資料"),
        current_user: User = Depends(get_current_user)
    ):
        """替換整個章節 - 包含所有內容區塊和子章節"""
        try:
            result = replace_section(
                user_id=current_user.id,
                article_id=article_id,
                section_id=request.section_id,
                updated_section=request
            )
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"error": str(e)})
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.delete("/{article_id}/sections/{section_id}", response_model=StandardResponse)
    async def remove_section(
        article_id: str = Path(...),
        section_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """刪除章節"""
        try:
            result = delete_section(current_user.id, article_id, section_id)
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    # ==================== 內容區塊管理 ====================

    @router.post("/{article_id}/sections/{section_id}/content", response_model=AddContentResponse)
    async def create_content(
        article_id: str = Path(...),
        section_id: str = Path(...),
        request: AddContentRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """新增內容區塊"""
        try:
            if request.content_type != "paragraph":
                raise InvalidContentTypeError(request.content_type, ["paragraph"])
            
            block_id, result = add_content_block(current_user.id, article_id, section_id, request.content, request.content_type)
            return AddContentResponse(block_id=block_id, message=result)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except (InvalidContentTypeError, ValidationError) as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.delete("/{article_id}/sections/{section_id}/content/{block_id}", response_model=StandardResponse)
    async def remove_content(
        article_id: str = Path(...),
        section_id: str = Path(...),
        block_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """刪除內容區塊"""
        try:
            result = delete_content_block(current_user.id, article_id, section_id, block_id)
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError, ContentBlockNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    # ==================== 快取和版本管理 ====================

    @router.post("/{article_id}/cache/invalidate", response_model=StandardResponse)
    async def invalidate_cache(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """清除文章快取"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            manager.invalidate_cache()
            return StandardResponse(message=f"Cache invalidated for article {article_id}", success=True)
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.post("/{article_id}/undo", response_model=StandardResponse)
    async def undo_article(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """復原上一個操作"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            success = manager.undo()
            
            if not success:
                return StandardResponse(message="Already at the first version", success=False)
            
            return StandardResponse(message="Successfully undone to previous version", success=True)
        except Exception as e:
            log.error(f"Undo error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{article_id}/redo", response_model=StandardResponse)
    async def redo_article(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """重做下一個操作"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            success = manager.redo()
            
            if not success:
                return StandardResponse(message="Already at the latest version", success=False)
            
            return StandardResponse(message="Successfully redone to next version", success=True)
        except Exception as e:
            log.error(f"Redo error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/{article_id}/title", response_model=StandardResponse)
    async def update_art_title(
        article_id: str = Path(..., description="文章 ID"),
        request: UpdateArticleTitleRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新文章標題"""
        try:
            result = update_article_title(current_user.id, article_id, request.new_title)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Update title error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})
    
    @router.patch("/{article_id}/prompt", response_model=StandardResponse)
    async def update_art_prompt(
        article_id: str = Path(..., description="文章 ID"),
        request: UpdateArticlePromptRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新文章生成提示詞"""
        try:
            result = update_article_prompt(current_user.id, article_id, request.article_prompt)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Update prompt error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})
    
    @router.post("/{article_id}/copy", response_model=CreateArticleResponse)
    async def copy_article(
        article_id: str = Path(..., description="要複製的文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """複製分享的文章到自己的帳號"""
        try:
            new_article_id = copy_article_to_user(
                source_article_id=article_id,
                target_user_id=current_user.id
            )
            return CreateArticleResponse(
                article_id=new_article_id,
                message="Article copied successfully"
            )
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            raise HTTPException(status_code=503, detail=e.to_dict())
        except Exception as e:
            log.error(f"Copy article error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})
    
    return router