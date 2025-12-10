"""Authentication Router - 提供登入與認證相關 API"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm

from article_copilot.configs.logger_setting import log
from article_copilot.configs.project_setting import security_config
from article_copilot.models.api.requests.auth_requests import LoginRequest
from article_copilot.models.api.responses.auth_responses import TokenResponse
from article_copilot.models.api.responses.common_responses import ErrorResponse
from article_copilot.security.login import get_access_token
from article_copilot.services.user import UserService


def create_auth_router() -> APIRouter:
    """建立認證 Router"""
    
    router = APIRouter()
    user_service = UserService()
    
    # OAuth2 相容的登入端點 (for Swagger UI)
    @router.post(
        "/login",
        response_model=TokenResponse,
        responses={
            401: {"model": ErrorResponse, "description": "認證失敗"},
            500: {"model": ErrorResponse, "description": "伺服器錯誤"}
        },
        summary="使用者登入 (OAuth2 相容)",
        description="使用 OAuth2 標準的 form-data 格式登入，適用於 Swagger UI"
    )
    async def login_oauth2(
        form_data: OAuth2PasswordRequestForm = Depends()
    ):
        """OAuth2 相容的登入端點 (使用 form-data)"""
        try:
            # 驗證使用者 (username 欄位用來傳遞 email)
            user = user_service.authenticate_user(
                form_data.username,  # OAuth2 標準使用 username
                form_data.password
            )
            
            if not user:
                log.warning(f"Login failed for: {form_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 生成 access token
            access_token_expires = timedelta(
                minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = get_access_token(
                user=user,
                expires_delta=access_token_expires
            )
            
            log.info(f"User logged in successfully: {user.email_address}")
            
            # 返回完整的 TokenResponse (必須包含 expires_in)
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": security_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 轉換為秒
            }
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during login"
            )
    
    # JSON 格式的登入端點 (for API clients)
    @router.post(
        "/login-json",
        response_model=TokenResponse,
        responses={
            401: {"model": ErrorResponse, "description": "認證失敗"},
            500: {"model": ErrorResponse, "description": "伺服器錯誤"}
        },
        summary="使用者登入 (JSON 格式)",
        description="使用 JSON 格式登入，適用於一般 API 客戶端"
    )
    async def login_json(
        login_request: LoginRequest = Body(...)
    ):
        """JSON 格式的登入端點"""
        try:
            user = user_service.authenticate_user(
                login_request.email_address,
                login_request.password
            )
            
            if not user:
                log.warning(f"Login failed for: {login_request.email_address}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "INVALID_CREDENTIALS",
                        "message": "Incorrect email or password"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(
                minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = get_access_token(
                user=user,
                expires_delta=access_token_expires
            )
            
            log.info(f"User logged in successfully: {user.email_address}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": security_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Unexpected error during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred during login"
                }
            )
    
    return router