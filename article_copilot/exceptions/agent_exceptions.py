"""Agent Related Exceptions - Agent 相關異常"""
from .base_exceptions import ServiceBaseException, ValidationError


class AgentError(ServiceBaseException):
    """Agent 錯誤的基礎類別"""
    pass


class LLMError(AgentError):
    """LLM 調用錯誤"""
    def __init__(self, reason: str = None):
        message = "LLM request failed"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="LLM_ERROR"
        )
        if reason:
            self.details["reason"] = reason


class ToolExecutionError(AgentError):
    """工具執行錯誤"""
    def __init__(self, tool_name: str, reason: str = None):
        message = f"Tool '{tool_name}' execution failed"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_ERROR"
        )
        self.details["tool_name"] = tool_name
        if reason:
            self.details["reason"] = reason


class PromptError(ValidationError):
    """Prompt 錯誤"""
    def __init__(self, prompt_name: str, reason: str):
        super().__init__(
            field="prompt",
            reason=reason,
            error_code="PROMPT_ERROR"
        )
        self.details["prompt_name"] = prompt_name


class TokenLimitExceededError(AgentError):
    """Token 限制超過"""
    def __init__(self, token_count: int, token_limit: int):
        message = f"Token count {token_count} exceeds limit {token_limit}"
        super().__init__(
            message=message,
            error_code="TOKEN_LIMIT_EXCEEDED"
        )
        self.details.update({
            "token_count": token_count,
            "token_limit": token_limit
        })