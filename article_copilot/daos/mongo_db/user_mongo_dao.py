from typing import Optional, List
from pymongo.errors import PyMongoError, DuplicateKeyError
from pymongo.database import Database
from datetime import datetime

from article_copilot.models.domain.user import User
from article_copilot.util.mongodb_client import get_mongodb_database


class MongoDBUserDAO:
    """
    MongoDB 使用者資料存取層
    負責使用者的持久化操作
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        初始化 DAO
        
        Args:
            db: MongoDB 資料庫實例,若不提供則使用預設連線
        """
        self.db = db or get_mongodb_database()
        self.users_collection = self.db["users"]
        
        # 建立索引以提升查詢效能
        self._create_indexes()
    
    def _create_indexes(self):
        """建立必要的索引"""
        try:
            # email_address 唯一索引
            self.users_collection.create_index(
                "email_address",
                unique=True,
                background=True
            )
            
            # 其他查詢索引
            self.users_collection.create_index(
                "authority",
                background=True
            )
            
            self.users_collection.create_index(
                "created_at",
                background=True
            )
            
            print("✓ MongoDB User 索引建立成功")
        except Exception as e:
            print(f"⚠ MongoDB User 索引建立警告: {e}")
    
    def save(self, user: User) -> bool:
        """
        儲存新使用者到 MongoDB
        
        Args:
            user: 要儲存的使用者物件
            
        Returns:
            bool: 操作是否成功
        """
        try:
            user_dict = user.model_dump()
            user_dict["_id"] = user_dict.pop("id")  # 使用 id 作為 MongoDB 的 _id
            user_dict["created_at"] = datetime.utcnow()
            user_dict["updated_at"] = datetime.utcnow()
            
            self.users_collection.insert_one(user_dict)
            
            print(f"✓ 使用者儲存成功 (id: {user.id})")
            return True
            
        except DuplicateKeyError:
            print(f"✗ 使用者已存在 (email: {user.email_address})")
            return False
        except PyMongoError as e:
            print(f"✗ 儲存使用者失敗 (id: {user.id}): {e}")
            return False
    
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        從 MongoDB 根據 ID 讀取使用者
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            User 物件或 None
        """
        try:
            user_dict = self.users_collection.find_one({"_id": user_id})
            
            if user_dict:
                user_dict["id"] = user_dict.pop("_id")  # 轉換 _id 為 id
                return User.model_validate(user_dict)
            
            return None
            
        except PyMongoError as e:
            print(f"✗ 讀取使用者失敗 (id: {user_id}): {e}")
            return None
    
    def find_by_email_address(self, email_address: str) -> Optional[User]:
        """
        從 MongoDB 根據 email 讀取使用者
        
        Args:
            email_address: 使用者 email
            
        Returns:
            User 物件或 None
        """
        try:
            user_dict = self.users_collection.find_one({"email_address": email_address})
            
            if user_dict:
                user_dict["id"] = user_dict.pop("_id")
                return User.model_validate(user_dict)
            
            return None
            
        except PyMongoError as e:
            print(f"✗ 讀取使用者失敗 (email: {email_address}): {e}")
            return None
    
    def find_all(self) -> Optional[List[User]]:
        """
        從 MongoDB 讀取所有使用者
        
        Returns:
            User 物件列表或 None
        """
        try:
            user_dicts = list(self.users_collection.find())
            
            if not user_dicts:
                return []
            
            users = []
            for user_dict in user_dicts:
                user_dict["id"] = user_dict.pop("_id")
                users.append(User.model_validate(user_dict))
            
            return users
            
        except PyMongoError as e:
            print(f"✗ 讀取所有使用者失敗: {e}")
            return None
    
    def update_by_id(self, user_id: str, user: User) -> Optional[User]:
        """
        更新使用者資料
        
        Args:
            user_id: 使用者 ID
            user: 更新的使用者物件
            
        Returns:
            更新後的 User 物件或 None
        """
        try:
            user_dict = user.model_dump(exclude={"id", "created_at"})
            user_dict["updated_at"] = datetime.utcnow()
            
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": user_dict}
            )
            
            if result.modified_count > 0:
                print(f"✓ 使用者更新成功 (id: {user_id})")
                return self.find_by_id(user_id)
            
            return None
            
        except PyMongoError as e:
            print(f"✗ 更新使用者失敗 (id: {user_id}): {e}")
            return None
    
    def update_password(self, user_id: str, hashed_password: str) -> Optional[User]:
        """
        更新使用者密碼
        
        Args:
            user_id: 使用者 ID
            hashed_password: 新的雜湊密碼
            
        Returns:
            更新後的 User 物件或 None
        """
        try:
            result = self.users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✓ 使用者密碼更新成功 (id: {user_id})")
                return self.find_by_id(user_id)
            
            return None
            
        except PyMongoError as e:
            print(f"✗ 更新密碼失敗 (id: {user_id}): {e}")
            return None
    
    def delete_by_id(self, user_id: str) -> bool:
        """
        從 MongoDB 刪除使用者
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            result = self.users_collection.delete_one({"_id": user_id})
            
            if result.deleted_count > 0:
                print(f"✓ 使用者刪除成功 (id: {user_id})")
                return True
            
            return False
            
        except PyMongoError as e:
            print(f"✗ 刪除使用者失敗 (id: {user_id}): {e}")
            return False
    
    def user_exists(self, user_id: str) -> bool:
        """
        檢查使用者是否存在
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            bool: 使用者是否存在
        """
        try:
            count = self.users_collection.count_documents(
                {"_id": user_id},
                limit=1
            )
            return count > 0
            
        except PyMongoError as e:
            print(f"✗ 檢查使用者存在性失敗 (id: {user_id}): {e}")
            return False


# --- 工廠函式 ---

_mongodb_user_dao_instance: Optional[MongoDBUserDAO] = None


def get_user_dao() -> MongoDBUserDAO:
    """
    取得 MongoDB User DAO 的單例實例
    
    Returns:
        MongoDBUserDAO 實例
    """
    global _mongodb_user_dao_instance
    
    if _mongodb_user_dao_instance is None:
        _mongodb_user_dao_instance = MongoDBUserDAO()
    
    return _mongodb_user_dao_instance