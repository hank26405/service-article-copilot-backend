"""This module contains class to for user service."""
from typing import List, Optional

from article_copilot.models.domain.user import User
from article_copilot.models.api.requests.user_requests import (
    CreateUserRequest, 
    UpdateUserRequest, 
    ChangePasswordRequest
)
from article_copilot.models.api.responses.user_responses import UserResponse
from article_copilot.security.login import generate_password, get_password_hash, verify_password
from article_copilot.util.function_utils import generate_id
from article_copilot.configs.logger_setting import log
from article_copilot.daos.mongo_db.user_mongo_dao import get_user_dao


class UserService:
    """Provide functions related to User entity."""
    
    def __init__(self):
        self.user_dao = get_user_dao()

    def create_user_with_authority(
        self, 
        create_user_request: CreateUserRequest, 
        authority: str
    ) -> Optional[UserResponse]:
        """Create an user with given authority."""
        # 生成密碼
        new_password = None
        if not create_user_request.password:
            new_password = generate_password()
            hashed_password = get_password_hash(new_password)
        else:
            hashed_password = get_password_hash(create_user_request.password)
        
        # 建立 User entity
        user = User(
            id=str(generate_id()),
            email_address=create_user_request.email_address,
            hashed_password=hashed_password,
            authority=authority,
            name=create_user_request.name
        )
        
        # 儲存到資料庫
        if not self.user_dao.save(user):
            log.error(f"Failed to save user: {user.email_address}")
            return None
        
        # 建立回應
        response = UserResponse(
            id=user.id,
            email_address=user.email_address,
            authority=user.authority,
            name=user.name
        )
        
        if new_password:
            response.additional_info = f"default password (please change): {new_password}"
        
        return response

    def find_all(self) -> Optional[List[UserResponse]]:
        """Get all users."""
        users = self.user_dao.find_all()
        if not users:
            return None
        
        return [
            UserResponse(
                id=user.id,
                email_address=user.email_address,
                authority=user.authority,
                name=user.name
            )
            for user in users
        ]

    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get the user based on provided user_id."""
        user = self.user_dao.find_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            email_address=user.email_address,
            authority=user.authority,
            name=user.name
        )

    def authenticate_user(self, email_address: str, password: str) -> Optional[User]:
        """Check user authentication."""
        user = self.user_dao.find_by_email_address(email_address)
        
        if not user:
            log.warning(f"User not found: {email_address}")
            return None
        
        if not verify_password(password, user.hashed_password):
            log.warning(f"Invalid password for user: {email_address}")
            return None
        
        return user
    
    def get_user_by_email_address(self, email_address: str) -> Optional[UserResponse]:
        """Get the user based on provided email_address."""
        user = self.user_dao.find_by_email_address(email_address)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            email_address=user.email_address,
            authority=user.authority,
            name=user.name
        )

    def update_user(
        self, 
        user_id: str, 
        update_user_request: UpdateUserRequest
    ) -> Optional[UserResponse]:
        """Update the user based on provided user_id."""
        existing_user = self.user_dao.find_by_id(user_id)
        if not existing_user:
            log.error(f"User not found: {user_id}")
            return None
        
        update_data = update_user_request.model_dump(exclude_unset=True)
        
        updated_user = User(
            id=existing_user.id,
            email_address=update_data.get("email_address", existing_user.email_address),
            hashed_password=existing_user.hashed_password,
            authority=existing_user.authority,
            name=update_data.get("name", existing_user.name),
            created_at=existing_user.created_at
        )
        
        result = self.user_dao.update_by_id(user_id, updated_user)
        if not result:
            log.error(f"Failed to update user: {user_id}")
            return None
        
        return UserResponse(
            id=result.id,
            email_address=result.email_address,
            authority=result.authority,
            name=result.name
        )

    def delete_user(self, user_id: str) -> bool:
        """Delete the user based on provided user_id."""
        success = self.user_dao.delete_by_id(user_id)
        if success:
            log.info(f"User deleted: {user_id}")
        else:
            log.error(f"Failed to delete user: {user_id}")
        return success

    def change_user_password(
        self, 
        change_password_request: ChangePasswordRequest, 
        user: User
    ) -> Optional[UserResponse]:
        """Change user's password after verifying its current password."""
        if not verify_password(
            change_password_request.current_password,
            user.hashed_password
        ):
            log.warning(f"Invalid current password for user: {user.id}")
            return None
        
        hashed_new_password = get_password_hash(change_password_request.new_password)
        
        updated_user = self.user_dao.update_password(user.id, hashed_new_password)
        if not updated_user:
            log.error(f"Failed to update password for user: {user.id}")
            return None
        
        log.info(f"Password changed successfully for user: {user.id}")
        return UserResponse(
            id=updated_user.id,
            email_address=updated_user.email_address,
            authority=updated_user.authority,
            name=updated_user.name
        )