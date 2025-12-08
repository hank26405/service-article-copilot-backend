from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

from article_copilot.configs.project_setting import security_config


class CreateUserRequest(BaseModel):
    """使用者建立請求"""
    email_address: EmailStr
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """驗證密碼強度"""
        if v is None:
            return v
        
        # 如果有設定密碼規則，則驗證
        if hasattr(security_config, 'PASSWORD_RULE_REGEX'):
            if not re.match(security_config.PASSWORD_RULE_REGEX, v):
                raise ValueError(
                    'Password must contain at least 8 characters, '
                    'including uppercase, lowercase, digit and special character'
                )
        return v


class UpdateUserRequest(BaseModel):
    """使用者更新請求"""
    email_address: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=100)


class ChangePasswordRequest(BaseModel):
    """變更密碼請求"""
    current_password: str = Field(..., description="目前密碼")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密碼")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """驗證新密碼強度"""
        if hasattr(security_config, 'PASSWORD_RULE_REGEX'):
            if not re.match(security_config.PASSWORD_RULE_REGEX, v):
                raise ValueError(
                    'Password must contain at least 8 characters, '
                    'including uppercase, lowercase, digit and special character'
                )
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password_different(cls, v: str, info) -> str:
        """確保新密碼與舊密碼不同"""
        if 'current_password' in info.data and v == info.data['current_password']:
            raise ValueError('New password must be different from current password')
        return v

