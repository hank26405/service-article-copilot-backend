"""This file is for application config"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    """Define config used by the service."""
    log_file_path: str = 'data/logs/'
    log_file_name: str = 'service_article_copilot.log'
    system_name: str = "service_article_copilot"
    secret_token: str = Field(default="EMPTY", validation_alias="SECRET_TOKEN")
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class SecurityConfig(BaseSettings):
    """Security configuration"""
    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")  # ✅ 必須在 .env 中設定
    ALGORITHM: str = Field(default="HS256", validation_alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    model_config = SettingsConfigDict(
        env_file="agent.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class GitHubAIConfig(BaseSettings):
    """Configuration for the GitHub AI service."""
    endpoint: str = Field(default="https://models.github.ai/inference", validation_alias="GITHUB_AI_ENDPOINT")
    token: str = Field(default="EMPTY", validation_alias="GITHUB_API_TOKEN")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class RAGConfig(BaseSettings):
    """Configuration for the RAG service."""
    vector_store_path: str = "data/vector_store"
    docs_path: str = "data/docs"
    model_name: str = Field(default="openai/text-embedding-3-small", validation_alias="RAG_MODEL_NAME")
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class LargeLLMConfig(BaseSettings):
    """Configuration for the Azure OpenAI Chat service."""
    model_name: str = Field(default="openai/gpt-4o", validation_alias="Large_LLM_MODEL_NAME")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class SmallLLMConfig(BaseSettings):
    """Configuration for the Azure OpenAI Chat service."""
    model_name: str = Field(default="openai/gpt-4.1-mini", validation_alias="Small_LLM_MODEL_NAME")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class Gemma327BLlmConfig(BaseSettings):
    api_key: str = "EMPTY"
    # base_url: str = "http://203.73.24.148:8110/v1"
    base_url: str = "http://192.168.1.123:8110/v1"
    model: str = "google/gemma-3-27b-it"
    temperature: float = 0.1
    max_retries: int = 2
    frequency_penalty: float = 0
    max_tokens: int = 1024

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class EmbeddingLlmConfig(BaseSettings):
    api_key: str = "EMPTY"
    # base_url: str = "http://203.73.24.148:8111/v1"
    base_url: str = "http://192.168.1.123:8111/v1"
    model: str = "Qwen/Qwen3-Embedding-4B"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )


class RedisConfigSettings(BaseSettings):
    """Redis configuration settings for caching and session storage."""
    host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    port: int = Field(default=6379, validation_alias="REDIS_PORT")
    password: Optional[str] = Field(default=None, validation_alias="REDIS_PASSWORD")
    db: int = Field(default=0, validation_alias="REDIS_DB")
    socket_timeout: int = Field(default=5, validation_alias="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(default=5, validation_alias="REDIS_SOCKET_CONNECT_TIMEOUT")
    max_connections: int = Field(default=50, validation_alias="REDIS_MAX_CONNECTIONS")
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class MongoDBConfigSettings(BaseSettings):
    """MongoDB configuration settings for persistent storage."""
    uri: str = Field(
        default="mongodb://my-mongo:27017/",
        validation_alias="MONGODB_URI"
    )
    database: str = Field(
        default="article_copilot",
        validation_alias="MONGODB_DATABASE"
    )
    # 連接池設定
    max_pool_size: int = Field(
        default=100,
        validation_alias="MONGODB_MAX_POOL_SIZE"
    )
    min_pool_size: int = Field(
        default=10,
        validation_alias="MONGODB_MIN_POOL_SIZE"
    )
    # 超時設定 (毫秒)
    server_selection_timeout_ms: int = Field(
        default=5000,
        validation_alias="MONGODB_SERVER_SELECTION_TIMEOUT_MS"
    )
    connect_timeout_ms: int = Field(
        default=5000,
        validation_alias="MONGODB_CONNECT_TIMEOUT_MS"
    )
    socket_timeout_ms: int = Field(
        default=5000,
        validation_alias="MONGODB_SOCKET_TIMEOUT_MS"
    )
    # 認證設定 (可選)
    username: Optional[str] = Field(
        default=None,
        validation_alias="MONGODB_USERNAME"
    )
    password: Optional[str] = Field(
        default=None,
        validation_alias="MONGODB_PASSWORD"
    )
    auth_source: str = Field(
        default="admin",
        validation_alias="MONGODB_AUTH_SOURCE"
    )
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class CacheConfig(BaseSettings):
    """Cache configuration for Cache-Aside Pattern."""
    # Redis 快取 TTL (秒)
    article_cache_ttl: int = Field(
        default=3600,
        validation_alias="CACHE_ARTICLE_TTL"
    )
    # 快取策略
    enable_write_through: bool = Field(
        default=False,
        validation_alias="CACHE_ENABLE_WRITE_THROUGH"
    )
    enable_read_through: bool = Field(
        default=True,
        validation_alias="CACHE_ENABLE_READ_THROUGH"
    )
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow"
    )

class PromptPathConfig(BaseSettings):
    """Configuration for the prompt paths."""
    image_prompt: str = Field(default="article_copilot/services/prompts/Image_prompt.md", validation_alias="PROMPT_IMAGE_PATH")
    text_prompt: str = Field(default="article_copilot/services/prompts/Text_prompt.md", validation_alias="PROMPT_TEXT_PATH")
    playwright_prompt: str = Field(default="article_copilot/services/prompts/Playwright_prompt.md", validation_alias="PROMPT_PLAYWRIGHT_PATH")

# 初始化設定
service_config = ServiceConfig()
rag_config = RAGConfig()
github_ai_config = GitHubAIConfig()
prompt_path_config = PromptPathConfig()
large_llm_config = LargeLLMConfig()
small_llm_config = SmallLLMConfig()
gemma3_27b_llm_config = Gemma327BLlmConfig()
embedding_llm_config = EmbeddingLlmConfig()
redis_config = RedisConfigSettings()
mongodb_config = MongoDBConfigSettings()
cache_config = CacheConfig()
security_config = SecurityConfig()