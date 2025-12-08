from typing import Optional, List
from pymongo.errors import PyMongoError
from pymongo.database import Database

from article_copilot.models.domain.article import Article
from article_copilot.util.mongodb_client import get_mongodb_database

class MongoDBArticleDAO:
    """
    MongoDB 文章資料存取層
    負責文章的持久化操作
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        初始化 DAO
        
        Args:
            db: MongoDB 資料庫實例,若不提供則使用預設連線
        """
        self.db = db or get_mongodb_database()
        self.articles_collection = self.db["articles"]
        self.user_articles_collection = self.db["user_articles"]
        
        # 建立索引以提升查詢效能
        self._create_indexes()
    
    def _create_indexes(self):
        """建立必要的索引"""
        try:
            # 文章集合的複合索引
            self.articles_collection.create_index(
                [("user_id", 1), ("article_id", 1)], 
                unique=True,
                background=True
            )
            self.articles_collection.create_index(
                "article_id",
                background=True
            )
            
            # 使用者文章列表的索引
            self.user_articles_collection.create_index(
                "user_id",
                unique=True,
                background=True
            )
            
            print("✓ MongoDB 索引建立成功")
        except Exception as e:
            print(f"⚠ MongoDB 索引建立警告: {e}")
    
    def save_article(self, article: Article) -> bool:
        """
        儲存或更新文章到 MongoDB
        
        Args:
            article: 要儲存的文章物件
            
        Returns:
            bool: 操作是否成功
        """
        try:
            article_dict = article.model_dump()
            
            # 使用 upsert 操作 (不存在則新增,存在則更新)
            result = self.articles_collection.update_one(
                {
                    "user_id": article.user_id,
                    "article_id": article.article_id
                },
                {"$set": article_dict},
                upsert=True
            )
            
            # 同時更新使用者的文章列表
            self.user_articles_collection.update_one(
                {"user_id": article.user_id},
                {
                    "$addToSet": {
                        "article_ids": article.article_id
                    }
                },
                upsert=True
            )
            
            return True
            
        except PyMongoError as e:
            print(f"✗ 儲存文章失敗 (user: {article.user_id}, article: {article.article_id}): {e}")
            return False
    
    def get_article(self, user_id: str, article_id: str) -> Optional[Article]:
        """
        從 MongoDB 讀取文章
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            Article 物件或 None
        """
        try:
            article_dict = self.articles_collection.find_one({
                "user_id": user_id,
                "article_id": article_id
            })
            
            if article_dict:
                # 移除 MongoDB 的 _id 欄位
                article_dict.pop('_id', None)
                return Article.model_validate(article_dict)
            
            return None
            
        except PyMongoError as e:
            print(f"✗ 讀取文章失敗 (user: {user_id}, article: {article_id}): {e}")
            return None
    
    def delete_article(self, user_id: str, article_id: str) -> bool:
        """
        從 MongoDB 刪除文章
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 刪除文章
            result = self.articles_collection.delete_one({
                "user_id": user_id,
                "article_id": article_id
            })
            
            # 從使用者文章列表中移除
            self.user_articles_collection.update_one(
                {"user_id": user_id},
                {"$pull": {"article_ids": article_id}}
            )
            
            return result.deleted_count > 0
            
        except PyMongoError as e:
            print(f"✗ 刪除文章失敗 (user: {user_id}, article: {article_id}): {e}")
            return False
    
    def get_user_article_ids(self, user_id: str) -> List[str]:
        """
        取得使用者的所有文章 ID
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            文章 ID 列表
        """
        try:
            user_doc = self.user_articles_collection.find_one({"user_id": user_id})
            
            if user_doc and "article_ids" in user_doc:
                return user_doc["article_ids"]
            
            return []
            
        except PyMongoError as e:
            print(f"✗ 讀取使用者文章列表失敗 (user: {user_id}): {e}")
            return []
    
    def article_exists(self, user_id: str, article_id: str) -> bool:
        """
        檢查文章是否存在
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            bool: 文章是否存在
        """
        try:
            count = self.articles_collection.count_documents({
                "user_id": user_id,
                "article_id": article_id
            }, limit=1)
            return count > 0
            
        except PyMongoError as e:
            print(f"✗ 檢查文章存在性失敗 (user: {user_id}, article: {article_id}): {e}")
            return False

# --- 工廠函式 ---

_mongodb_article_dao_instance: Optional[MongoDBArticleDAO] = None

def get_article_dao() -> MongoDBArticleDAO:
    """
    取得 MongoDB Article DAO 的單例實例
    
    Returns:
        MongoDBArticleDAO 實例
    """
    global _mongodb_article_dao_instance
    
    if _mongodb_article_dao_instance is None:
        _mongodb_article_dao_instance = MongoDBArticleDAO()
    
    return _mongodb_article_dao_instance