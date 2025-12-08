"""Redis client service for managing Redis connections."""

import redis # type: ignore
from typing import Optional
from article_copilot.configs.project_setting import redis_config
from article_copilot.configs.logger_setting import log


class RedisClient:
    """Redis 客戶端管理器."""
    
    _instance: Optional['RedisClient'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls) -> 'RedisClient':
        """單例模式確保只有一個 Redis 連接實例."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 Redis 客戶端."""
        if self._redis_client is None:
            self._connect()
    
    def _connect(self):
        """建立 Redis 連接."""
        try:
            connection_params = {
                'host': redis_config.host,
                'port': redis_config.port,
                'db': redis_config.db,
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            }
            
            # 如果有密碼，添加密碼參數
            if redis_config.password:
                connection_params['password'] = redis_config.password
            
            self._redis_client = redis.Redis(**connection_params)
            
            # 測試連接
            if self._redis_client:
                self._redis_client.ping()
                log.info(f"Redis 連接成功: {redis_config.host}:{redis_config.port}")
            
        except Exception as e:
            log.warning(f"Redis 連接失敗: {e}")
            self._redis_client = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """獲取 Redis 客戶端實例."""
        if self._redis_client is None:
            self._connect()
        return self._redis_client
    
    def is_connected(self) -> bool:
        """檢查 Redis 是否連接."""
        if self._redis_client is None:
            return False
        
        try:
            self._redis_client.ping()
            return True
        except Exception as e:
            log.warning(f"Redis 連接檢查失敗: {e}")
            return False
    
    def reconnect(self):
        """重新連接 Redis."""
        log.info("嘗試重新連接 Redis...")
        self._redis_client = None
        self._connect()
    
    def close(self):
        """關閉 Redis 連接."""
        if self._redis_client:
            try:
                self._redis_client.close()
                log.info("Redis 連接已關閉")
            except Exception as e:
                log.error(f"關閉 Redis 連接失敗: {e}")
            finally:
                self._redis_client = None


# 全局 Redis 客戶端實例
redis_client = RedisClient()

def get_redis_client() -> Optional[redis.Redis]:
    """獲取 Redis 客戶端的便捷函數."""
    return redis_client.get_client()