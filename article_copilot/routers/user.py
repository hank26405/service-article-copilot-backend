"""User Management Router - 提供使用者的增刪改查 API"""
# pylint: disable=unused-variable,blacklisted-name,consider-using-enumerate
from typing import List
from fastapi import APIRouter, HTTPException, Security, status, Path, Query, Body, Depends

from article_copilot.configs.logger_setting import log
from article_copilot.enum.auth import Authorities
from article_copilot.security.auth import get_current_user

# 匯入 Models
from article_copilot.models.domain.user import User
from article_copilot.models.api.requests.user_requests import (
    CreateUserRequest,
    UpdateUserRequest,
    ChangePasswordRequest
)
from article_copilot.models.api.responses.user_responses import UserResponse
from article_copilot.models.api.responses.common_responses import (
    StandardResponse,
    ErrorResponse
)

# 匯入 Service
from article_copilot.services.user import UserService


def create_user_router() -> APIRouter:
    """建立使用者管理 Router"""
    
    router = APIRouter()
    user_service = UserService()
    
    # ==================== 使用者 CRUD ====================

    @router.post(
        "/",
        response_model=UserResponse,
        responses={
            400: {"model": ErrorResponse, "description": "驗證錯誤"},
            409: {"model": ErrorResponse, "description": "使用者已存在"},
            500: {"model": ErrorResponse, "description": "伺服器錯誤"}
        },
        summary="建立新使用者",
        description="建立一個新的一般使用者 (需要管理員權限)"
    )
    async def create_user(
        create_user_request: CreateUserRequest = Body(...),
        current_user: User = Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
    ):
        """建立新使用者 (管理員專用)"""
        try:
            # 檢查使用者是否已存在
            existing_user = user_service.get_user_by_email_address(create_user_request.email_address)
            if existing_user:
                log.warning(f"User already exists: {create_user_request.email_address}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "USER_ALREADY_EXISTS",
                        "message": f"User with email {create_user_request.email_address} already exists"
                    }
                )
            
            # 建立使用者
            created_user = user_service.create_user_with_authority(
                create_user_request, 
                Authorities.MEMBER_USER
            )
            
            if not created_user:
                log.error(f"Failed to create user: {create_user_request.email_address}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "USER_CREATION_FAILED",
                        "message": "Could not create user"
                    }
                )
            
            log.info(f"User created successfully: {created_user.id}")
            return created_user
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when creating user: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred"
                }
            )

    @router.get(
        "/",
        response_model=List[UserResponse],
        responses={
            500: {"model": ErrorResponse, "description": "伺服器錯誤"}
        },
        summary="取得所有使用者",
        description="取得系統中所有使用者的列表 (需要管理員權限)"
    )
    async def get_all_users(
        current_user: User = Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
    ):
        """取得所有使用者 (管理員專用)"""
        try:
            users = user_service.find_all()
            if users is None:
                log.error("Failed to retrieve users")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "USERS_RETRIEVAL_FAILED",
                        "message": "Could not get users"
                    }
                )
            
            return users
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when getting users: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred"
                }
            )

    @router.get(
        "/me",
        response_model=UserResponse,
        summary="取得當前使用者資訊",
        description="取得目前登入使用者的資訊"
    )
    async def get_current_user_info(
        current_user: User = Depends(get_current_user)
    ):
        """取得當前使用者資訊"""
        try:
            return UserResponse(
                id=current_user.id,
                email_address=current_user.email_address,
                authority=current_user.authority,
                name=current_user.name
            )
        except Exception as e:
            log.error(f"Unexpected error when getting current user info: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to retrieve user information"
                }
            )

    @router.get(
        "/{user_id}",
        response_model=UserResponse,
        responses={
            404: {"model": ErrorResponse, "description": "使用者不存在"}
        },
        summary="取得指定使用者",
        description="根據使用者 ID 取得使用者資訊"
    )
    async def get_user(
        user_id: str = Path(..., description="使用者 ID"),
        current_user: User = Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
    ):
        """取得指定使用者 (管理員專用)"""
        try:
            user = user_service.get_user_by_id(user_id)
            if not user:
                log.info(f"User not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "USER_NOT_FOUND",
                        "message": f"User with id {user_id} not found"
                    }
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when getting user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to retrieve user"
                }
            )

    @router.put(
        "/{user_id}",
        response_model=UserResponse,
        responses={
            404: {"model": ErrorResponse, "description": "使用者不存在"},
            400: {"model": ErrorResponse, "description": "驗證錯誤"}
        },
        summary="更新使用者資訊",
        description="更新指定使用者的資訊 (需要管理員權限)"
    )
    async def update_user(
        user_id: str = Path(..., description="使用者 ID"),
        update_user_request: UpdateUserRequest = Body(...),
        current_user: User = Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
    ):
        """更新使用者資訊 (管理員專用)"""
        try:
            updated_user = user_service.update_user(user_id, update_user_request)
            if not updated_user:
                log.error(f"Failed to update user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "USER_UPDATE_FAILED",
                        "message": f"Could not update user with id {user_id}"
                    }
                )
            
            log.info(f"User updated successfully: {user_id}")
            return updated_user
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when updating user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to update user"
                }
            )

    @router.delete(
        "/{user_id}",
        response_model=StandardResponse,
        responses={
            404: {"model": ErrorResponse, "description": "使用者不存在"}
        },
        summary="刪除使用者",
        description="刪除指定的使用者 (需要管理員權限)"
    )
    async def delete_user(
        user_id: str = Path(..., description="使用者 ID"),
        current_user: User = Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
    ):
        """刪除使用者 (管理員專用)"""
        try:
            # 防止管理員刪除自己
            if user_id == current_user.id:
                log.warning(f"Admin attempted to delete themselves: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "CANNOT_DELETE_SELF",
                        "message": "Cannot delete your own account"
                    }
                )
            
            success = user_service.delete_user(user_id)
            if not success:
                log.error(f"Failed to delete user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "USER_DELETION_FAILED",
                        "message": f"Could not delete user with id {user_id}"
                    }
                )
            
            log.info(f"User deleted successfully: {user_id}")
            return StandardResponse(
                message=f"User {user_id} deleted successfully",
                success=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when deleting user {user_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to delete user"
                }
            )

    # ==================== 密碼管理 ====================

    @router.post(
        "/me/change-password",
        response_model=StandardResponse,
        responses={
            400: {"model": ErrorResponse, "description": "驗證錯誤"},
            401: {"model": ErrorResponse, "description": "當前密碼錯誤"}
        },
        summary="變更密碼",
        description="變更當前使用者的密碼"
    )
    async def change_password(
        change_password_request: ChangePasswordRequest = Body(...),
        current_user: User = Depends(get_current_user)
    ):
        """變更當前使用者密碼"""
        try:
            updated_user = user_service.change_user_password(
                change_password_request,
                current_user
            )
            
            if not updated_user:
                log.warning(f"Password change failed for user: {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "INVALID_CURRENT_PASSWORD",
                        "message": "Current password is incorrect"
                    }
                )
            
            log.info(f"Password changed successfully for user: {current_user.id}")
            return StandardResponse(
                message="Password changed successfully",
                success=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error when changing password: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to change password"
                }
            )

    return router
