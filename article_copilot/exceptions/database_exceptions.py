"""Database Related Exceptions - 資料庫相關異常"""
from typing import Optional
from .base_exceptions import ServiceBaseException


class DatabaseError(ServiceBaseException):
    """資料庫錯誤的基礎類別"""
    pass


class DatabaseConnectionError(DatabaseError):
    """資料庫連線錯誤"""
    def __init__(self, database_type: str, reason: Optional[str] = None):
        message = f"Failed to connect to {database_type}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR"
        )
        self.details["database_type"] = database_type
        if reason:
            self.details["reason"] = reason


class MongoDBConnectionError(DatabaseConnectionError):
    """MongoDB 連線錯誤"""
    def __init__(self, reason: Optional[str] = None):
        super().__init__("MongoDB", reason)
        self.error_code = "MONGODB_CONNECTION_ERROR"


class RedisConnectionError(DatabaseConnectionError):
    """Redis 連線錯誤"""
    def __init__(self, reason: Optional[str] = None):
        super().__init__("Redis", reason)
        self.error_code = "REDIS_CONNECTION_ERROR"


class DatabaseOperationError(DatabaseError):
    """資料庫操作錯誤"""
    def __init__(self, operation: str, database_type: str, reason: Optional[str] = None):
        message = f"Failed to {operation} in {database_type}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="DATABASE_OPERATION_ERROR"
        )
        self.details.update({
            "operation": operation,
            "database_type": database_type
        })
        if reason:
            self.details["reason"] = reason


class CacheError(DatabaseError):
    """快取相關錯誤"""
    def __init__(self, operation: str, reason: Optional[str] = None):
        message = f"Cache {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="CACHE_ERROR"
        )
        self.details["operation"] = operation
        if reason:
            self.details["reason"] = reason


class TransactionError(DatabaseError):
    """交易錯誤"""
    def __init__(self, reason: str):
        message = f"Transaction failed: {reason}"
        super().__init__(
            message=message,
            error_code="TRANSACTION_ERROR"
        )
        self.details["reason"] = reason