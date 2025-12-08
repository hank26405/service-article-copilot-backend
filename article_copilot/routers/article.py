"""Article CRUD Router - 提供文章的增刪改查 API"""
import re
import json
from typing import List
from article_copilot.models.api.responses.article_responses import ArticleStructureResponse
from fastapi import APIRouter, HTTPException, Path, Body, Depends

from article_copilot.configs.logger_setting import log
from article_copilot.models.domain.user import User
from article_copilot.security.auth import get_current_user

from article_copilot.services.article_manager import (
    create_new_article,
    export_article_as_json,
    list_sections,
    list_my_articles,
    add_main_section,
    add_subsection,
    add_paragraph,
    update_section_title,
    update_paragraph,
    delete_section,
    delete_content_block,
    delete_article,
    ArticleManager
)

# 匯入異常
from article_copilot.exceptions import (
    ArticleNotFoundError,
    SectionNotFoundError,
    ContentBlockNotFoundError,
    DatabaseConnectionError,
    DatabaseOperationError,
    InvalidContentTypeError,
    ValidationError,
    ServiceBaseException
)

# 使用統一匯出
from article_copilot.models import (
    # Domain
    Article,
    
    # Requests
    CreateArticleRequest,
    AddSectionRequest,
    UpdateSectionTitleRequest,
    AddContentRequest,
    UpdateContentRequest,
    
    # Responses
    CreateArticleResponse,
    ArticleSummary,
    ArticlesTitleResponse,
    AddSectionResponse,
    AddContentResponse,
    StandardResponse,
    ErrorResponse,
    CacheInfoResponse,
)


def create_article_router() -> APIRouter:
    """建立文章管理 Router"""
    
    router = APIRouter()
    
    # ==================== 文章 CRUD ====================

    @router.post(
        "/articles",
        response_model=CreateArticleResponse,
        responses={
            400: {"model": ErrorResponse, "description": "驗證錯誤"},
            500: {"model": ErrorResponse, "description": "伺服器錯誤"},
            503: {"model": ErrorResponse, "description": "資料庫連線失敗"}
        },
        summary="建立新文章",
        description="為當前使用者建立一篇新文章"
    )
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
            log.warning(f"Validation error when creating article: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except DatabaseOperationError as e:
            log.error(f"Database operation error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when creating article: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}
            )

    @router.get(
        "/articles",
        response_model=List[ArticlesTitleResponse],
        responses={
            503: {"model": ErrorResponse, "description": "資料庫連線失敗"}
        },
        summary="取得使用者的文章列表",
        description="取得當前使用者的所有文章"
    )
    async def get_articles(
        current_user: User = Depends(get_current_user)
    ):
        """取得使用者的文章列表"""
        try:
            return list_my_articles(current_user.id)
        except DatabaseConnectionError as e:
            log.error(f"Database connection error when listing articles: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error when listing articles: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when listing articles for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to retrieve articles"}
            )

    @router.get(
        "/articles/{article_id}/json",
        response_model=dict,
        responses={
            404: {"model": ErrorResponse, "description": "文章不存在"}
        },
        summary="匯出文章為 JSON",
        description="將文章完整內容匯出為 JSON 格式"
    )
    async def export_article(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """匯出文章為 JSON"""
        try:
            result = export_article_as_json(current_user.id, article_id)
            return json.loads(result)
        except ArticleNotFoundError as e:
            log.info(f"Article not found for export: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except json.JSONDecodeError as e:
            log.error(f"JSON decode error: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "JSON_DECODE_ERROR", "message": "Failed to parse article JSON"}
            )
        except Exception as e:
            log.error(f"Unexpected error when exporting article {article_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to export article"}
            )

    @router.delete(
        "/articles/{article_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章不存在"}
        },
        summary="刪除文章",
        description="刪除指定的文章及其所有內容"
    )
    async def remove_article(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """刪除文章"""
        try:
            result = delete_article(current_user.id, article_id)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            log.info(f"Article not found for deletion: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when deleting article {article_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to delete article"}
            )

    # ==================== 章節管理 ====================

    @router.get(
        "/articles/{article_id}/sections",
        response_model=ArticleStructureResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章不存在"}
        },
        summary="取得文章章節結構",
        description="取得文章的完整章節層級結構 (JSON 格式)"
    )
    async def get_sections(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """取得文章章節結構"""
        try:
            structure = list_sections(current_user.id, article_id)
            return structure
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when listing sections: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to list sections"}
            )

    @router.post(
        "/articles/{article_id}/sections",
        response_model=AddSectionResponse,
        responses={
            400: {"model": ErrorResponse, "description": "驗證錯誤"},
            404: {"model": ErrorResponse, "description": "文章或父章節不存在"}
        },
        summary="新增章節",
        description="新增主章節或子章節"
    )
    async def create_section(
        article_id: str = Path(..., description="文章 ID"),
        request: AddSectionRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """新增章節"""
        try:
            if request.parent_section_id:
                section_id, result = add_subsection(current_user.id, article_id, request.parent_section_id, request.title)
            else:
                section_id, result = add_main_section(current_user.id, article_id, request.title)

            return AddSectionResponse(
                section_id=section_id,
                message=result
            )
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Parent section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            log.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when creating section: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to create section"}
            )

    @router.patch(
        "/articles/{article_id}/sections/{section_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章或章節不存在"}
        },
        summary="更新章節標題",
        description="更新指定章節的標題"
    )
    async def update_section(
        article_id: str = Path(..., description="文章 ID"),
        section_id: str = Path(..., description="章節 ID"),
        request: UpdateSectionTitleRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新章節標題"""
        try:
            result = update_section_title(current_user.id, article_id, section_id, request.new_title)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            log.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when updating section: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to update section"}
            )

    @router.delete(
        "/articles/{article_id}/sections/{section_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章或章節不存在"}
        },
        summary="刪除章節",
        description="刪除指定章節及其所有子章節和內容"
    )
    async def remove_section(
        article_id: str = Path(..., description="文章 ID"),
        section_id: str = Path(..., description="章節 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """刪除章節"""
        try:
            result = delete_section(current_user.id, article_id, section_id)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when deleting section: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to delete section"}
            )

    # ==================== 內容區塊管理 ====================

    @router.post(
        "/articles/{article_id}/content",
        response_model=AddContentResponse,
        responses={
            400: {"model": ErrorResponse, "description": "驗證錯誤"},
            404: {"model": ErrorResponse, "description": "文章或章節不存在"}
        },
        summary="新增內容區塊",
        description="在指定章節中新增段落內容"
    )
    async def create_content(
        article_id: str = Path(..., description="文章 ID"),
        request: AddContentRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """新增內容區塊"""
        try:
            if request.content_type != "paragraph":
                raise InvalidContentTypeError(request.content_type, ["paragraph"])
            
            block_id, result = add_paragraph(current_user.id, article_id, request.section_id, request.content)

            return AddContentResponse(
                block_id=block_id,
                message=result
            )
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except InvalidContentTypeError as e:
            log.warning(f"Invalid content type: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except ValidationError as e:
            log.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when creating content: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to create content"}
            )

    @router.patch(
        "/articles/{article_id}/sections/{section_id}/content/{block_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章、章節或內容區塊不存在"}
        },
        summary="更新內容區塊",
        description="更新指定的段落內容"
    )
    async def update_content(
        article_id: str = Path(..., description="文章 ID"),
        section_id: str = Path(..., description="章節 ID"),
        block_id: str = Path(..., description="內容區塊 ID"),
        request: UpdateContentRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新內容區塊"""
        try:
            result = update_paragraph(current_user.id, article_id, section_id, block_id, request.content)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ContentBlockNotFoundError as e:
            log.info(f"Content block not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            log.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when updating content: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to update content"}
            )

    @router.delete(
        "/articles/{article_id}/sections/{section_id}/content/{block_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章、章節或內容區塊不存在"}
        },
        summary="刪除內容區塊",
        description="刪除指定的內容區塊"
    )
    async def remove_content(
        article_id: str = Path(..., description="文章 ID"),
        section_id: str = Path(..., description="章節 ID"),
        block_id: str = Path(..., description="內容區塊 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """刪除內容區塊"""
        try:
            result = delete_content_block(current_user.id, article_id, section_id, block_id)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except SectionNotFoundError as e:
            log.info(f"Section not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ContentBlockNotFoundError as e:
            log.info(f"Content block not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when deleting content: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to delete content"}
            )

    # ==================== 快取管理 ====================

    @router.post(
        "/articles/{article_id}/cache/invalidate",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "文章不存在"}
        },
        summary="清除文章快取",
        description="手動清除指定文章的 Redis 快取"
    )
    async def invalidate_cache(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """清除文章快取"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            manager.invalidate_cache()
            
            return StandardResponse(
                message=f"Cache invalidated for article {article_id}",
                success=True
            )
        except ArticleNotFoundError as e:
            log.info(f"Article not found: {e}")
            raise HTTPException(status_code=404, detail=e.to_dict())
        except DatabaseConnectionError as e:
            log.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=e.to_dict())
        except ServiceBaseException as e:
            log.error(f"Service error: {e}")
            raise HTTPException(status_code=500, detail=e.to_dict())
        except Exception as e:
            log.error(f"Unexpected error when invalidating cache: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Failed to invalidate cache"}
            )

    @router.post(
        "/articles/{article_id}/undo",
        response_model=StandardResponse,
        summary="復原上一個操作",
        description="回復到上一個儲存的版本"
    )
    async def undo_article(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """復原上一個操作"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            success = manager.undo()
            
            if not success:
                return StandardResponse(
                    message="Already at the first version",
                    success=False
                )
            
            return StandardResponse(
                message="Successfully undone to previous version",
                success=True
            )
        except Exception as e:
            log.error(f"Undo error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/articles/{article_id}/redo",
        response_model=StandardResponse,
        summary="重做下一個操作",
        description="前進到下一個儲存的版本"
    )
    async def redo_article(
        article_id: str = Path(..., description="文章 ID"),
        current_user: User = Depends(get_current_user)
    ):
        """重做下一個操作"""
        try:
            manager = ArticleManager(current_user.id, article_id)
            success = manager.redo()
            
            if not success:
                return StandardResponse(
                    message="Already at the latest version",
                    success=False
                )
            
            return StandardResponse(
                message="Successfully redone to next version",
                success=True
            )
        except Exception as e:
            log.error(f"Redo error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    return router