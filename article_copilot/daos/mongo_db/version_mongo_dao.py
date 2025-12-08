"""Version MongoDB DAO - 文章版本資料存取層"""
from typing import List, Optional
from pymongo.errors import PyMongoError
from pymongo.database import Database
from pymongo import DESCENDING, ASCENDING

from article_copilot.models.domain.article_version import ArticleVersion
from article_copilot.util.mongodb_client import get_mongodb_database
from article_copilot.configs.logger_setting import log

# 版本控制配置
MAX_VERSIONS_PER_ARTICLE = 20  # 每篇文章最多保留 20 個版本


class MongoDBVersionDAO:
    """
    MongoDB 版本資料存取層
    負責文章版本的持久化操作
    使用滑動窗口策略管理版本數量
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        初始化 DAO
        
        Args:
            db: MongoDB 資料庫實例,若不提供則使用預設連線
        """
        self.db = db or get_mongodb_database()
        self.versions_collection = self.db["article_versions"]
        
        # 建立索引以提升查詢效能
        self._create_indexes()
    
    def _create_indexes(self):
        """建立必要的索引"""
        try:
            # 複合索引: user_id + article_id + version_number (唯一)
            self.versions_collection.create_index(
                [("user_id", ASCENDING), ("article_id", ASCENDING), ("version_number", DESCENDING)],
                unique=True,
                name="user_article_version_idx",
                background=True
            )
            
            # 索引: user_id + article_id + timestamp (用於清理舊版本)
            self.versions_collection.create_index(
                [("user_id", ASCENDING), ("article_id", ASCENDING), ("timestamp", DESCENDING)],
                name="user_article_timestamp_idx",
                background=True
            )
            
            print("✓ Version MongoDB 索引建立成功")
        except Exception as e:
            print(f"⚠ Version MongoDB 索引建立警告: {e}")
    
    def save_version(self, version: ArticleVersion) -> bool:
        """
        儲存版本 - 自動清理超過限制的舊版本
        
        Args:
            version: 要儲存的版本物件
            
        Returns:
            bool: 操作是否成功
        """
        try:
            version_dict = version.model_dump()
            
            # 儲存新版本
            self.versions_collection.insert_one(version_dict)
            
            # 檢查並清理超過限制的版本
            self._cleanup_old_versions(version.user_id, version.article_id)
            
            log.info(f"Version {version.version_number} saved for article {version.article_id}")
            return True
            
        except PyMongoError as e:
            log.error(f"✗ 儲存版本失敗 (user: {version.user_id}, article: {version.article_id}, version: {version.version_number}): {e}")
            return False
    
    def _cleanup_old_versions(self, user_id: str, article_id: str):
        """
        清理超過限制的舊版本 (保留最新的 MAX_VERSIONS_PER_ARTICLE 個)
        使用滑動窗口策略
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
        """
        try:
            # 計算總版本數
            total_versions = self.versions_collection.count_documents({
                "user_id": user_id,
                "article_id": article_id
            })
            
            # 如果超過限制,刪除最舊的版本
            if total_versions > MAX_VERSIONS_PER_ARTICLE:
                versions_to_delete = total_versions - MAX_VERSIONS_PER_ARTICLE
                
                # 找出最舊的版本
                old_versions = list(self.versions_collection.find(
                    {"user_id": user_id, "article_id": article_id},
                    {"version_number": 1}
                ).sort("version_number", ASCENDING).limit(versions_to_delete))
                
                # 刪除舊版本
                version_numbers_to_delete = [v["version_number"] for v in old_versions]
                
                result = self.versions_collection.delete_many({
                    "user_id": user_id,
                    "article_id": article_id,
                    "version_number": {"$in": version_numbers_to_delete}
                })
                
                log.info(f"Cleaned up {result.deleted_count} old versions for article {article_id}")
                
        except PyMongoError as e:
            log.error(f"✗ 清理舊版本失敗 (user: {user_id}, article: {article_id}): {e}")
    
    def get_version_by_number(
        self,
        user_id: str,
        article_id: str,
        version_number: int
    ) -> Optional[ArticleVersion]:
        """
        根據版本號取得特定版本
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            version_number: 版本號
            
        Returns:
            ArticleVersion 物件或 None
        """
        try:
            version_dict = self.versions_collection.find_one({
                "user_id": user_id,
                "article_id": article_id,
                "version_number": version_number
            })
            
            if version_dict:
                # 移除 MongoDB 的 _id 欄位
                version_dict.pop("_id", None)
                return ArticleVersion.model_validate(version_dict)
            
            return None
            
        except PyMongoError as e:
            log.error(f"✗ 讀取版本失敗 (user: {user_id}, article: {article_id}, version: {version_number}): {e}")
            return None
    
    def get_latest_version(self, user_id: str, article_id: str) -> Optional[ArticleVersion]:
        """
        取得最新版本
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            最新的 ArticleVersion 物件或 None
        """
        try:
            version_dict = self.versions_collection.find_one(
                {"user_id": user_id, "article_id": article_id},
                sort=[("version_number", DESCENDING)]
            )
            
            if version_dict:
                # 移除 MongoDB 的 _id 欄位
                version_dict.pop("_id", None)
                return ArticleVersion.model_validate(version_dict)
            
            return None
            
        except PyMongoError as e:
            log.error(f"✗ 讀取最新版本失敗 (user: {user_id}, article: {article_id}): {e}")
            return None
    
    def get_all_versions(self, user_id: str, article_id: str) -> List[ArticleVersion]:
        """
        取得文章的所有版本 (按版本號降序排列)
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            ArticleVersion 列表
        """
        try:
            version_dicts = self.versions_collection.find(
                {"user_id": user_id, "article_id": article_id}
            ).sort("version_number", DESCENDING)
            
            versions = []
            for version_dict in version_dicts:
                version_dict.pop("_id", None)
                versions.append(ArticleVersion.model_validate(version_dict))
            
            return versions
            
        except PyMongoError as e:
            log.error(f"✗ 讀取所有版本失敗 (user: {user_id}, article: {article_id}): {e}")
            return []
    
    def delete_versions_after(self, user_id: str, article_id: str, version_number: int) -> int:
        """
        刪除指定版本之後的所有版本 (用於 redo 後新增操作)
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            version_number: 版本號
            
        Returns:
            int: 刪除的版本數量
        """
        try:
            result = self.versions_collection.delete_many({
                "user_id": user_id,
                "article_id": article_id,
                "version_number": {"$gt": version_number}
            })
            
            log.info(f"Deleted {result.deleted_count} versions after version {version_number}")
            return result.deleted_count
            
        except PyMongoError as e:
            log.error(f"✗ 刪除版本失敗 (user: {user_id}, article: {article_id}, after version: {version_number}): {e}")
            return 0
    
    def delete_all_versions(self, user_id: str, article_id: str) -> int:
        """
        刪除文章的所有版本 (用於刪除文章時)
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            int: 刪除的版本數量
        """
        try:
            result = self.versions_collection.delete_many({
                "user_id": user_id,
                "article_id": article_id
            })
            
            log.info(f"Deleted all {result.deleted_count} versions for article {article_id}")
            return result.deleted_count
            
        except PyMongoError as e:
            log.error(f"✗ 刪除所有版本失敗 (user: {user_id}, article: {article_id}): {e}")
            return 0
    



# --- 工廠函式 ---

_mongodb_version_dao_instance: Optional[MongoDBVersionDAO] = None


def get_version_dao() -> MongoDBVersionDAO:
    """
    取得 MongoDB Version DAO 的單例實例
    
    Returns:
        MongoDBVersionDAO 實例
    """
    global _mongodb_version_dao_instance
    
    if _mongodb_version_dao_instance is None:
        _mongodb_version_dao_instance = MongoDBVersionDAO()
    
    return _mongodb_version_dao_instance


def reset_version_dao():
    """重置 Version DAO 單例 (主要用於測試)"""
    global _mongodb_version_dao_instance
    _mongodb_version_dao_instance = None