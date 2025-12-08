"""Exceptions Package - 統一匯出所有異常類別"""

# Base Exceptions
from .base_exceptions import (
    ServiceBaseException,
    NotFoundError,
    ValidationError,
    ConflictError,
    PermissionError
)

# Article Exceptions
from .article_exceptions import (
    ArticleNotFoundError,
    SectionNotFoundError,
    ContentBlockNotFoundError,
    ArticleAlreadyExistsError,
    InvalidArticleOperationError,
    ArticleTitleTooLongError,
    EmptyArticleTitleError,
    SectionLevelExceededError,
    InvalidContentTypeError
)

# Database Exceptions
from .database_exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    MongoDBConnectionError,
    RedisConnectionError,
    DatabaseOperationError,
    CacheError,
    TransactionError
)

# RAG Exceptions
from .rag_exceptions import (
    DocumentNotFoundError,
    VectorStoreError,
    EmbeddingError,
    DocumentProcessingError,
    UnsupportedFileTypeError
)

# Agent Exceptions
from .agent_exceptions import (
    AgentError,
    LLMError,
    ToolExecutionError,
    PromptError,
    TokenLimitExceededError
)

__all__ = [
    # Base
    "ServiceBaseException",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "PermissionError",
    
    # Article
    "ArticleNotFoundError",
    "SectionNotFoundError",
    "ContentBlockNotFoundError",
    "ArticleAlreadyExistsError",
    "InvalidArticleOperationError",
    "ArticleTitleTooLongError",
    "EmptyArticleTitleError",
    "SectionLevelExceededError",
    "InvalidContentTypeError",
    
    # Database
    "DatabaseError",
    "DatabaseConnectionError",
    "MongoDBConnectionError",
    "RedisConnectionError",
    "DatabaseOperationError",
    "CacheError",
    "TransactionError",
    
    # RAG
    "DocumentNotFoundError",
    "VectorStoreError",
    "EmbeddingError",
    "DocumentProcessingError",
    "UnsupportedFileTypeError",
    
    # Agent
    "AgentError",
    "LLMError",
    "ToolExecutionError",
    "PromptError",
    "TokenLimitExceededError",
]