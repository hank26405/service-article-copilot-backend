"""RAG Related Exceptions - RAG 相關異常"""
from .base_exceptions import NotFoundError, ValidationError, ServiceBaseException


class DocumentNotFoundError(NotFoundError):
    """文件不存在"""
    def __init__(self, document_id: str):
        super().__init__(
            resource_type="Document",
            resource_id=document_id,
            error_code="DOCUMENT_NOT_FOUND"
        )


class VectorStoreError(ServiceBaseException):
    """向量儲存錯誤"""
    def __init__(self, operation: str, reason: str = None):
        message = f"Vector store {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="VECTOR_STORE_ERROR"
        )
        self.details["operation"] = operation
        if reason:
            self.details["reason"] = reason


class EmbeddingError(ServiceBaseException):
    """嵌入向量生成錯誤"""
    def __init__(self, reason: str = None):
        message = "Failed to generate embeddings"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR"
        )
        if reason:
            self.details["reason"] = reason


class DocumentProcessingError(ServiceBaseException):
    """文件處理錯誤"""
    def __init__(self, filename: str, reason: str = None):
        message = f"Failed to process document '{filename}'"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="DOCUMENT_PROCESSING_ERROR"
        )
        self.details["filename"] = filename
        if reason:
            self.details["reason"] = reason


class UnsupportedFileTypeError(ValidationError):
    """不支援的檔案類型"""
    def __init__(self, file_type: str, supported_types: list):
        reason = f"File type '{file_type}' not supported. Supported types: {supported_types}"
        super().__init__(
            field="file_type",
            reason=reason,
            error_code="UNSUPPORTED_FILE_TYPE"
        )
        self.details.update({
            "file_type": file_type,
            "supported_types": supported_types
        })