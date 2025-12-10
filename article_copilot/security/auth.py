"""This module contains functions to get and check authentication information."""
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt

from article_copilot.configs.project_setting import security_config
from article_copilot.models.domain.auth import TokenData
from article_copilot.models.domain.user import User
from article_copilot.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
user_service = UserService()


def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token and check if the security scopes match,
        typically called by FastAPI.Depends or FastAPI.Security.

        Parameters:
            security_scopes: the required scopes.
            token: JWT token get from request header.

        Returns:
            user: the User object parsed from the JWT token.

        Raises:
            HTTPException: Raises a 401_UNAUTHORIZED if the token can not be validate,
                           or the scopes do not match.

        Examples:
            Requires to use the API with the authority of ADMIN_GROUP:
                >>> Security(get_current_user, scopes=[Authorities.SYS_ADMIN])
            Requires no authorities to use the API:
                >>> Depends(get_current_user)
    """
    authenticate_header = "Bearer"
    if security_scopes.scopes:
        authenticate_header += f' scope="{security_scopes.scope_str}"'

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_header},
    )

    try:
        payload = jwt.decode(token, security_config.SECRET_KEY, algorithms=[security_config.ALGORITHM])
        email_address: str = payload.get("sub")
        if email_address is None:
            raise credentials_exception
        token_data = TokenData(**payload)
    except JWTError:
        raise credentials_exception

    if not _check_scopes(security_scopes.scopes, token_data.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_header},
        )

    user_entity = user_service.user_dao.find_by_email_address(email_address)
    if not user_entity:
        raise credentials_exception
    
    return user_entity


def _check_scopes(expected_scopes: List[str], actual_scopes: List[str]) -> bool:
    """Check if all the expected scopes match to the actual ones.

        Parameters:
            expected_scopes: the required scopes.
            actual_scopes: the actual scopes from token.

        Returns:
            True if the scopes matched, else False.
    """
    actual_scopes_set = set(actual_scopes)
    for scope in expected_scopes:
        if scope not in actual_scopes_set:
            return False

    return True

