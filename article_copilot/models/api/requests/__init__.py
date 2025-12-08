"""API Request Models"""
from .article_requests import CreateArticleRequest, UpdateArticleTitleRequest
from .section_requests import AddSectionRequest, UpdateSectionTitleRequest
from .content_requests import AddContentRequest, UpdateContentRequest

__all__ = [
    "CreateArticleRequest",
    "UpdateArticleTitleRequest",
    "AddSectionRequest",
    "UpdateSectionTitleRequest",
    "AddContentRequest",
    "UpdateContentRequest",
]