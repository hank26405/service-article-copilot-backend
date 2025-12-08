"""Base Exception Classes - 基礎異常類別定義"""
from typing import Optional, Dict, Any


class ServiceBaseException(Exception):
    """
    服務層基礎異常類別
    所有自定義異常都應繼承此類別
    """
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化異常
        
        :param message: 錯誤訊息
        :param error_code: 錯誤代碼 (用於前端識別)
        :param details: 額外的錯誤細節
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式,方便 API 回應"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class NotFoundError(ServiceBaseException):
    """資源不存在的基礎異常"""
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, **kwargs)
        self.details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class ValidationError(ServiceBaseException):
    """驗證錯誤的基礎異常"""
    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Validation failed for field '{field}': {reason}"
        super().__init__(message, **kwargs)
        self.details.update({
            "field": field,
            "reason": reason
        })


class ConflictError(ServiceBaseException):
    """資源衝突的基礎異常"""
    pass


class PermissionError(ServiceBaseException):
    """權限錯誤的基礎異常"""
    pass