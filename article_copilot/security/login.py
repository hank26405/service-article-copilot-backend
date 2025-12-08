"""This module contains functions to deal with password and generate token."""
from datetime import datetime, timedelta
from typing import Optional
import random
import string

from jose import jwt
from passlib.context import CryptContext

from article_copilot.configs.project_setting import security_config
from article_copilot.models.domain.auth import TokenData
from article_copilot.models.domain.user import User
from article_copilot.enum.auth import Authorities

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the plain password is the same as the hashed password.

        Parameters:
            plain_password: plain text password
            hashed_password: hashed password to compare

        Returns:
            True if the password matched the hash, else False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(plain_password: str) -> str:
    """Get the hashed password with CryptContext.hash().
    
        Parameters:
            plain_password: plain text password to hash
            
        Returns:
            hashed password string
    """
    return pwd_context.hash(plain_password)


def generate_password() -> str:
    """Generate a random password with 8-12 characters.
    
    Password contains at least:
    - One lowercase letter
    - One uppercase letter
    - One digit
    - May contain special characters (@$!%*?&)
    
    Returns:
        Generated password string
    """
    # 密碼的長度在 8 到 12 之間隨機選擇
    length = random.randint(8, 12)
    
    # 確保包含至少一個小寫字母、一個大寫字母、一個數字
    lower = random.choice(string.ascii_lowercase)
    upper = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    
    # 剩餘的字符從大小寫字母、數字和特殊字符中隨機選擇
    all_characters = string.ascii_letters + string.digits + "@$!%*?&"
    remaining_length = length - 3
    remaining_chars = ''.join(random.choice(all_characters) for _ in range(remaining_length))
    
    # 將所有字符組合在一起並打亂順序
    password = list(lower + upper + digit + remaining_chars)
    random.shuffle(password)
    
    return ''.join(password)


def get_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Get access token from the user information.

        Parameters:
            user: an User object of target user.
            expires_delta: a datetime.timedelta object that shows how long the access token expires.

        Returns:
            an access token string.
    """
    issued = datetime.utcnow()
    if expires_delta:
        expire = issued + expires_delta
    else:
        expire = issued + timedelta(minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES)

    scopes = [user.authority]
    if user.authority == Authorities.SYS_ADMIN:
        scopes.append(Authorities.MEMBER_USER)
        
    token_data = TokenData(
        sub=user.email_address,
        scopes=scopes,
        user_id=str(user.id),
        iat=issued,
        exp=expire
    )
    encoded_jwt = jwt.encode(
        token_data.model_dump(), 
        security_config.SECRET_KEY, 
        algorithm=security_config.ALGORITHM
    )
    return encoded_jwt
