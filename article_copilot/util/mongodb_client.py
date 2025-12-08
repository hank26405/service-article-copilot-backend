from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from article_copilot.configs.project_setting import mongodb_config

class MongoDBConnection:
    """
    MongoDB 連線管理單例類
    負責管理全域的 MongoDB 連線
    """
    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化時不立即連線,採用延遲初始化"""
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """建立 MongoDB 連線"""
        try:
            # 建立連接字串
            connection_options = {
                "serverSelectionTimeoutMS": mongodb_config.server_selection_timeout_ms,
                "connectTimeoutMS": mongodb_config.connect_timeout_ms,
                "socketTimeoutMS": mongodb_config.socket_timeout_ms,
                "maxPoolSize": mongodb_config.max_pool_size,
                "minPoolSize": mongodb_config.min_pool_size,
            }
            
            # 如果有認證資訊,加入認證參數
            if mongodb_config.username and mongodb_config.password:
                connection_options.update({
                    "username": mongodb_config.username,
                    "password": mongodb_config.password,
                    "authSource": mongodb_config.auth_source,
                })
            
            # 建立客戶端
            self._client = MongoClient(
                mongodb_config.uri,
                **connection_options
            )
            
            # 測試連接
            self._client.admin.command('ping')
            self._database = self._client[mongodb_config.database]
            
            print(f"✓ MongoDB 連接成功")
            print(f"  資料庫: {mongodb_config.database}")
            print(f"  URI: {mongodb_config.uri}")
            print(f"  連接池大小: {mongodb_config.min_pool_size}-{mongodb_config.max_pool_size}")
            
        except ConnectionFailure as e:
            print(f"✗ MongoDB 連接失敗: {e}")
            self._client = None
            self._database = None
            raise
        except Exception as e:
            print(f"✗ MongoDB 初始化錯誤: {e}")
            self._client = None
            self._database = None
            raise
    
    @property
    def client(self) -> MongoClient:
        """取得 MongoDB 客戶端"""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def database(self) -> Database:
        """取得資料庫實例"""
        if self._database is None:
            self._connect()
        return self._database
    
    def close(self):
        """關閉連線"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            print("MongoDB 連接已關閉")
    
    def is_connected(self) -> bool:
        """檢查是否已連線"""
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False

# --- 工廠函式 ---

_mongodb_connection: Optional[MongoDBConnection] = None

def get_mongodb_connection() -> MongoDBConnection:
    """
    取得 MongoDB 連線的單例實例
    
    Returns:
        MongoDBConnection 實例
    """
    global _mongodb_connection
    if _mongodb_connection is None:
        _mongodb_connection = MongoDBConnection()
    return _mongodb_connection

def get_mongodb_client() -> MongoClient:
    """
    取得 MongoDB 客戶端
    
    Returns:
        MongoClient 實例
    """
    return get_mongodb_connection().client

def get_mongodb_database() -> Database:
    """
    取得 MongoDB 資料庫實例
    
    Returns:
        Database 實例
    """
    return get_mongodb_connection().database