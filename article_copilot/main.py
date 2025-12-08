"""This file creates the fastapi service with dependency injection and lifecycle management."""
# coding=utf-8
import os
from contextlib import asynccontextmanager
from article_copilot.routers.article import create_article_router
from article_copilot.routers.user import create_user_router
from article_copilot.util.init_database import initialize_database
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from article_copilot.routers.health_check import create_health_check_router
from article_copilot.configs.logger_setting import log
from article_copilot.util import function_utils

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    log.info("Starting application...")
    initialize_database()  # 初始化資料庫
    yield
    # 關閉時執行
    log.info("Shutting down application...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="智慧化文章助理 API",
        description="此 API 提供智慧化文章助理相關功能，包括代理服務、提示管理、RAG 文件管理、文章編輯服務等。",
        version=function_utils.health_check_parsing(),
        lifespan=lifespan, # 使用新的生命週期管理器
        root_path=os.getenv("ROOT_PATH", "/llm"),
        # docs_url=None,  # 禁用 Swagger UI
        # redoc_url=None,  # 禁用 ReDoc
        # openapi_url=None,  # 禁用 OpenAPI schema 端點
    )

    # 註冊 Routers，並傳入已經實例化的服務
    api_version = "/v1"
    
    app.include_router(
        create_health_check_router(),
        prefix=f"{api_version}/service",
        tags=["Health Check"]
    )
    # 註冊用戶和文章路由
    app.include_router(
        create_user_router(),
        prefix="/api/v1",
        tags=["Users"]
    )
    app.include_router(
        create_article_router(),
        prefix="/api/v1",
        tags=["Articles"]
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({
                'errCode': '400_BAD_REQUEST',
                'errMsg': 'Invalid Input',
                'errDetail': exc.errors()
            }),
        )

    return app

# 讓 uvicorn 可以直接運行此檔案
app = create_app()