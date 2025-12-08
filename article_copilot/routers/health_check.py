"""Health check router."""

from fastapi import APIRouter
from article_copilot.util.function_utils import health_check_parsing


def create_health_check_router() -> APIRouter:
    """Create health check router."""
    router = APIRouter()

    @router.get("/health_check")
    async def health_check():
        """Health check endpoint."""
        try:
            version = health_check_parsing()
            return {
                "status": "healthy",
                "version": version,
                "service": "microgrid-nchu-llm"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "version": "unknown"
            }

    return router
