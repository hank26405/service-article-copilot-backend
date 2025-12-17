"""Models Package - 統一匯出入口"""

# Domain Models
from article_copilot.models.domain.article import Article
from article_copilot.models.domain.section import Section
from article_copilot.models.domain.content_block import ContentBlock
from article_copilot.models.domain.article_version import ArticleVersion

# API Request Models
from .api.requests.article_requests import CreateArticleRequest, UpdateArticleTitleRequest
from .api.requests.section_requests import AddSectionRequest
from .api.requests.content_requests import AddContentRequest, UpdateContentRequest

# API Response Models
from .api.responses.article_responses import (
    CreateArticleResponse,
    ArticleSummary,
    ArticlesTitleResponse
)
from .api.responses.section_responses import AddSectionResponse
from .api.responses.content_responses import AddContentResponse
from .api.responses.common_responses import (
    StandardResponse,
    ErrorResponse,
    CacheInfoResponse
)

__all__ = [
    # Domain Models
    "Article",
    "Section",
    "ContentBlock",
    "ImageContent",
    "ChartContent",
    "ArticleVersion",
    
    # API Requests
    "CreateArticleRequest",
    "UpdateArticleTitleRequest",
    "AddSectionRequest",
    "AddContentRequest",
    "UpdateContentRequest",
    
    # API Responses
    "CreateArticleResponse",
    "ArticleSummary",
    "ArticlesTitleResponse",
    "AddSectionResponse",
    "AddContentResponse",
    "StandardResponse",
    "ErrorResponse",
    "CacheInfoResponse",
]