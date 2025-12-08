from typing import Optional
import redis
from redis.exceptions import RedisError

from article_copilot.models.domain.article import Article
from article_copilot.services.operators.redis_client import get_redis_client
from article_copilot.configs.project_setting import cache_config

class RedisArticleDAO:
    """
    Redis 文章快取資料存取層
    負責文章的快取操作
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, ttl: Optional[int] = None):
        """
        初始化 Redis DAO
        
        Args:
            redis_client: Redis 客戶端實例,若不提供則使用預設連線
            ttl: 快取過期時間(秒),若不提供則使用配置檔設定
        """
        self.redis = redis_client or get_redis_client()
        self.ttl = ttl or cache_config.article_cache_ttl
        self.key_prefix = "article"
    
    def _build_key(self, user_id: str, article_id: str) -> str:
        """
        建立 Redis key
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            完整的 Redis key
        """
        return f"{self.key_prefix}:{user_id}:{article_id}"
    
    def get_article(self, user_id: str, article_id: str) -> Optional[Article]:
        """
        從 Redis 快取讀取文章
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            Article 物件或 None
        """
        if not self.redis:
            return None
        
        try:
            key = self._build_key(user_id, article_id)
            article_json = self.redis.get(key)
            
            if article_json:
                print(f"✓ [Redis Cache Hit] 從快取讀取文章: {article_id}")
                return Article.model_validate_json(article_json)
            
            print(f"○ [Redis Cache Miss] 快取未命中: {article_id}")
            return None
            
        except RedisError as e:
            print(f"✗ Redis 讀取失敗 (user: {user_id}, article: {article_id}): {e}")
            return None
        except Exception as e:
            print(f"✗ 解析文章資料失敗: {e}")
            return None
    
    def save_article(self, article: Article) -> bool:
        """
        將文章儲存到 Redis 快取
        
        Args:
            article: 要快取的文章物件
            
        Returns:
            bool: 操作是否成功
        """
        if not self.redis:
            return False
        
        try:
            key = self._build_key(article.user_id, article.article_id)
            article_json = article.model_dump_json()
            
            # 使用 SETEX 設定 key 並指定過期時間
            self.redis.setex(key, self.ttl, article_json)
            
            print(f"✓ [Redis Cache Write] 文章已寫入快取: {article.article_id} (TTL: {self.ttl}s)")
            return True
            
        except RedisError as e:
            print(f"✗ Redis 寫入失敗 (user: {article.user_id}, article: {article.article_id}): {e}")
            return False
    
    def delete_article(self, user_id: str, article_id: str) -> bool:
        """
        從 Redis 快取刪除文章
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            bool: 操作是否成功
        """
        if not self.redis:
            return False
        
        try:
            key = self._build_key(user_id, article_id)
            result = self.redis.delete(key)
            
            if result > 0:
                print(f"✓ [Redis Cache Delete] 快取已清除: {article_id}")
                return True
            else:
                print(f"○ [Redis Cache Delete] 快取不存在: {article_id}")
                return False
            
        except RedisError as e:
            print(f"✗ Redis 刪除失敗 (user: {user_id}, article: {article_id}): {e}")
            return False
    
    def exists(self, user_id: str, article_id: str) -> bool:
        """
        檢查文章是否在快取中
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            bool: 是否存在於快取
        """
        if not self.redis:
            return False
        
        try:
            key = self._build_key(user_id, article_id)
            return self.redis.exists(key) > 0
        except RedisError as e:
            print(f"✗ Redis EXISTS 檢查失敗: {e}")
            return False
    
    def get_ttl(self, user_id: str, article_id: str) -> int:
        """
        取得快取的剩餘過期時間
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            剩餘秒數,-1 表示永不過期,-2 表示不存在
        """
        if not self.redis:
            return -2
        
        try:
            key = self._build_key(user_id, article_id)
            return self.redis.ttl(key)
        except RedisError as e:
            print(f"✗ Redis TTL 查詢失敗: {e}")
            return -2
    
    def refresh_ttl(self, user_id: str, article_id: str) -> bool:
        """
        重新整理快取的過期時間
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            bool: 操作是否成功
        """
        if not self.redis:
            return False
        
        try:
            key = self._build_key(user_id, article_id)
            result = self.redis.expire(key, self.ttl)
            
            if result:
                print(f"✓ [Redis TTL Refresh] 快取過期時間已更新: {article_id}")
            return result
            
        except RedisError as e:
            print(f"✗ Redis TTL 更新失敗: {e}")
            return False
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        清除使用者的所有文章快取
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            int: 刪除的 key 數量
        """
        if not self.redis:
            return 0
        
        try:
            pattern = f"{self.key_prefix}:{user_id}:*"
            keys = self.redis.keys(pattern)
            
            if keys:
                deleted = self.redis.delete(*keys)
                print(f"✓ [Redis Batch Delete] 已清除使用者 {user_id} 的 {deleted} 個快取")
                return deleted
            
            return 0
            
        except RedisError as e:
            print(f"✗ Redis 批量刪除失敗: {e}")
            return 0
    
    def get_cache_info(self, user_id: str, article_id: str) -> dict:
        """
        取得快取資訊
        
        Args:
            user_id: 使用者 ID
            article_id: 文章 ID
            
        Returns:
            快取資訊字典
        """
        return {
            "exists": self.exists(user_id, article_id),
            "ttl": self.get_ttl(user_id, article_id),
            "key": self._build_key(user_id, article_id)
        }

# --- 工廠函式 ---

_redis_article_dao_instance: Optional[RedisArticleDAO] = None

def get_redis_article_dao(ttl: int = 3600) -> RedisArticleDAO:
    """
    取得 Redis Article DAO 的單例實例
    
    Args:
        ttl: 快取過期時間(秒)
        
    Returns:
        RedisArticleDAO 實例
    """
    global _redis_article_dao_instance
    
    if _redis_article_dao_instance is None:
        _redis_article_dao_instance = RedisArticleDAO(ttl=ttl)
    
    return _redis_article_dao_instance