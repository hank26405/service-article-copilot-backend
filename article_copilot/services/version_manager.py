from typing import List, Optional, Tuple
from article_copilot.models import Article
from article_copilot.models.domain.article_version import ArticleVersion
from article_copilot.daos.mongo_db.version_mongo_dao import get_version_dao
from article_copilot.exceptions.article_exceptions import VersionNotFoundError

class VersionManager:
    """文章版本控制管理器"""
    
    def __init__(self, user_id: str, article_id: str):
        self.user_id = user_id
        self.article_id = article_id
        self.version_dao = get_version_dao()
        self.current_version_number = self._get_current_version_number()
        self.max_version_number = self.current_version_number
    
    def _get_current_version_number(self) -> int:
        """取得目前最新版本號"""
        latest = self.version_dao.get_latest_version(self.user_id, self.article_id)
        return latest.version_number if latest else 0
    
    def save_version(self, article: Article, operation: str, operation_desc: str) -> ArticleVersion:
        """儲存新版本"""
        # 如果當前不在最新版本,刪除之後的版本 (實現真正的線性 undo/redo)
        if self.current_version_number < self.max_version_number:
            self.version_dao.delete_versions_after(
                self.user_id, 
                self.article_id, 
                self.current_version_number
            )
        
        # 建立新版本
        new_version_number = self.current_version_number + 1
        version = ArticleVersion(
            article_id=article.article_id,
            user_id=article.user_id,
            version_number=new_version_number,
            snapshot=article.model_dump(),
            operation=operation,
            operation_desc=operation_desc
        )
        
        self.version_dao.save_version(version)
        self.current_version_number = new_version_number
        self.max_version_number = new_version_number
        
        return version
    
    def undo(self) -> Optional[Article]:
        """回到上一個版本"""
        if self.current_version_number <= 1:
            return None  # 已經是第一個版本
        
        target_version = self.current_version_number - 1
        version = self.version_dao.get_version_by_number(
            self.user_id, 
            self.article_id, 
            target_version
        )
        
        if not version:
            raise VersionNotFoundError(target_version, self.article_id, self.user_id)

        self.current_version_number = target_version
        return Article(**version.snapshot)
    
    def redo(self) -> Optional[Article]:
        """回到下一個版本"""
        if self.current_version_number >= self.max_version_number:
            return None  # 已經是最新版本
        
        target_version = self.current_version_number + 1
        version = self.version_dao.get_version_by_number(
            self.user_id, 
            self.article_id, 
            target_version
        )
        
        if not version:
            raise VersionNotFoundError(target_version, self.article_id, self.user_id)
        
        self.current_version_number = target_version
        return Article(**version.snapshot)
    
    
    def can_undo(self) -> bool:
        """是否可以 undo"""
        return self.current_version_number > 1
    
    def can_redo(self) -> bool:
        """是否可以 redo"""
        return self.current_version_number < self.max_version_number