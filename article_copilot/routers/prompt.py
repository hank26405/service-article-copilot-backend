"""Prompt Management Router - 提示詞管理 API"""
from fastapi import APIRouter, HTTPException, Path, Body, Depends

from article_copilot.configs.logger_setting import log
from article_copilot.models.domain.user import User
from article_copilot.security.auth import get_current_user

from article_copilot.services.prompt_manager import (
    update_article_prompt,
    update_section_prompt,
    update_content_block_prompt,
    toggle_article_fixed,
    toggle_section_fixed,
    toggle_content_block_fixed,
)

from article_copilot.exceptions import (
    ArticleNotFoundError,
    SectionNotFoundError,
    ContentBlockNotFoundError,
    ValidationError,
)

from article_copilot.models import (
    StandardResponse,
    ErrorResponse,
)

from article_copilot.models.api.requests.article_requests import UpdatePromptRequest


def create_prompt_router() -> APIRouter:
    """建立提示詞管理 Router"""
    
    router = APIRouter()

    # ==================== Prompt 管理 ====================

    @router.patch(
        "/{article_id}/prompt",
        response_model=StandardResponse,
        responses={404: {"model": ErrorResponse}},
        summary="更新文章提示詞"
    )
    async def update_article_prompt_endpoint(
        article_id: str = Path(...),
        request: UpdatePromptRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新文章提示詞"""
        try:
            result = update_article_prompt(current_user.id, article_id, request.new_prompt)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.patch(
        "/{article_id}/sections/{section_id}/prompt",
        response_model=StandardResponse,
        summary="更新章節提示詞"
    )
    async def update_section_prompt_endpoint(
        article_id: str = Path(...),
        section_id: str = Path(...),
        request: UpdatePromptRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新章節提示詞"""
        try:
            result = update_section_prompt(current_user.id, article_id, section_id, request.new_prompt)
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.patch(
        "/{article_id}/sections/{section_id}/content/{block_id}/prompt",
        response_model=StandardResponse,
        summary="更新內容區塊提示詞"
    )
    async def update_content_block_prompt_endpoint(
        article_id: str = Path(...),
        section_id: str = Path(...),
        block_id: str = Path(...),
        request: UpdatePromptRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """更新內容區塊提示詞"""
        try:
            result = update_content_block_prompt(
                current_user.id, article_id, section_id, block_id, request.new_prompt
            )
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError, ContentBlockNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    # ==================== Fixed 狀態管理 ====================

    @router.post(
        "/{article_id}/toggle-fixed",
        response_model=StandardResponse,
        summary="切換文章固定狀態"
    )
    async def toggle_article_fixed_endpoint(
        article_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """切換文章固定狀態"""
        try:
            result = toggle_article_fixed(current_user.id, article_id)
            return StandardResponse(message=result, success=True)
        except ArticleNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.post(
        "/{article_id}/sections/{section_id}/toggle-fixed",
        response_model=StandardResponse,
        summary="切換章節固定狀態"
    )
    async def toggle_section_fixed_endpoint(
        article_id: str = Path(...),
        section_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """切換章節固定狀態"""
        try:
            result = toggle_section_fixed(current_user.id, article_id, section_id)
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    @router.post(
        "/{article_id}/sections/{section_id}/content/{block_id}/toggle-fixed",
        response_model=StandardResponse,
        summary="切換內容區塊固定狀態"
    )
    async def toggle_content_block_fixed_endpoint(
        article_id: str = Path(...),
        section_id: str = Path(...),
        block_id: str = Path(...),
        current_user: User = Depends(get_current_user)
    ):
        """切換內容區塊固定狀態"""
        try:
            result = toggle_content_block_fixed(current_user.id, article_id, section_id, block_id)
            return StandardResponse(message=result, success=True)
        except (ArticleNotFoundError, SectionNotFoundError, ContentBlockNotFoundError) as e:
            raise HTTPException(status_code=404, detail=e.to_dict())
        except Exception as e:
            log.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail={"error": "INTERNAL_SERVER_ERROR"})

    return router