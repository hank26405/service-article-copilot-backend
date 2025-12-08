"""Article Related Exceptions - 文章相關異常"""
from typing import Optional
from .base_exceptions import NotFoundError, ValidationError, ConflictError, ServiceBaseException


class ArticleNotFoundError(NotFoundError):
    """文章不存在"""
    def __init__(self, article_id: str, user_id: str = None):
        super().__init__(
            resource_type="Article",
            resource_id=article_id,
            error_code="ARTICLE_NOT_FOUND"
        )
        if user_id:
            self.details["user_id"] = user_id


class SectionNotFoundError(NotFoundError):
    """章節不存在"""
    def __init__(self, section_id: str, article_id: str = None):
        super().__init__(
            resource_type="Section",
            resource_id=section_id,
            error_code="SECTION_NOT_FOUND"
        )
        if article_id:
            self.details["article_id"] = article_id


class ContentBlockNotFoundError(NotFoundError):
    """內容區塊不存在"""
    def __init__(self, block_id: str, section_id: str = None):
        super().__init__(
            resource_type="ContentBlock",
            resource_id=block_id,
            error_code="CONTENT_BLOCK_NOT_FOUND"
        )
        if section_id:
            self.details["section_id"] = section_id


class ArticleAlreadyExistsError(ConflictError):
    """文章已存在"""
    def __init__(self, article_id: str):
        message = f"Article with ID '{article_id}' already exists"
        super().__init__(
            message=message,
            error_code="ARTICLE_ALREADY_EXISTS"
        )
        self.details["article_id"] = article_id


class InvalidArticleOperationError(ValidationError):
    """無效的文章操作"""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            field=operation,
            reason=reason,
            error_code="INVALID_ARTICLE_OPERATION"
        )


class ArticleTitleTooLongError(ValidationError):
    """文章標題太長"""
    def __init__(self, title: str, max_length: int = 200):
        reason = f"Title length {len(title)} exceeds maximum {max_length}"
        super().__init__(
            field="title",
            reason=reason,
            error_code="ARTICLE_TITLE_TOO_LONG"
        )
        self.details.update({
            "title_length": len(title),
            "max_length": max_length
        })


class EmptyArticleTitleError(ValidationError):
    """文章標題為空"""
    def __init__(self):
        super().__init__(
            field="title",
            reason="Title cannot be empty",
            error_code="EMPTY_ARTICLE_TITLE"
        )


class SectionLevelExceededError(ValidationError):
    """章節層級超過限制"""
    def __init__(self, current_level: int, max_level: int = 6):
        reason = f"Section level {current_level} exceeds maximum {max_level}"
        super().__init__(
            field="section_level",
            reason=reason,
            error_code="SECTION_LEVEL_EXCEEDED"
        )
        self.details.update({
            "current_level": current_level,
            "max_level": max_level
        })


class InvalidContentTypeError(ValidationError):
    """無效的內容類型"""
    def __init__(self, content_type: str, allowed_types: list):
        reason = f"Content type '{content_type}' not in allowed types: {allowed_types}"
        super().__init__(
            field="content_type",
            reason=reason,
            error_code="INVALID_CONTENT_TYPE"
        )
        self.details.update({
            "content_type": content_type,
            "allowed_types": allowed_types
        })

class VersionNotFoundError(ServiceBaseException):
    """版本不存在異常"""
    def __init__(self, version_number: int, article_id: Optional[str] = None, user_id: Optional[str] = None):
        message = f"Version {version_number} not found"
        if article_id:
            message += f" for article '{article_id}'"
        if user_id:
            message += f" (user: '{user_id}')"
        super().__init__(
            message, 
            "VERSION_NOT_FOUND", 
            {"version_number": version_number, "article_id": article_id, "user_id": user_id}
        )
