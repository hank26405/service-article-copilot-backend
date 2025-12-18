"""Article Manager Service - 文章管理服務層"""
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from article_copilot.daos.mongo_db.version_mongo_dao import get_version_dao
from article_copilot.models.api.responses.article_responses import ArticlesTitleResponse
from langchain.tools import tool

# 匯入資料模型
from article_copilot.models import (Article, ContentBlock, Section)

# 匯入 DAO 層
from article_copilot.daos.mongo_db.article_mongo_dao import get_article_dao
from article_copilot.daos.redis.article_redis_dao import get_redis_article_dao

# 匯入異常
from article_copilot.exceptions import (
    ArticleNotFoundError,
    SectionNotFoundError,
    ContentBlockNotFoundError,
    DatabaseConnectionError,
    InvalidContentTypeError,
    DatabaseOperationError
)

# --- Cache-Aside Pattern 配置 ---
REDIS_CACHE_TTL = 3600  # Redis 快取過期時間 (秒)

# --- 多使用者文件管理器服務 (Cache-Aside Pattern 版本) ---

from article_copilot.services.version_manager import VersionManager

class ArticleManager:
    """
    一個基於 Cache-Aside Pattern 的多使用者文章管理服務。
    - Redis 作為快取層,提供快速讀取
    - MongoDB 作為持久化層,保證資料不丟失
    """

    def __init__(self, user_id: str, article_id: str, enable_versioning: bool = True):
        """
        初始化管理器。

        :param user_id: 進行操作的使用者 ID。
        :param article_id: 要操作的文件 ID。
        :raises DatabaseConnectionError: 當 Redis 和 MongoDB 都無法連接時
        :raises ArticleNotFoundError: 當文章不存在時
        """
        self.redis_dao = get_redis_article_dao(ttl=REDIS_CACHE_TTL)
        self.mongodb_dao = get_article_dao()
        
        if not self.redis_dao.redis and not self.mongodb_dao:
            raise DatabaseConnectionError("Both", "Redis and MongoDB are unavailable")
        
        self.user_id = user_id
        self.article_id = article_id
        self.article = self._load_article()
        
        # 版本控制
        self.enable_versioning = enable_versioning
        if enable_versioning:
            self.version_manager = VersionManager(user_id, article_id)

    def _load_article(self) -> Article:
        """
        使用 Cache-Aside Pattern 載入文章
        
        :raises ArticleNotFoundError: 當文章不存在時
        """
        # 步驟 1: 嘗試從 Redis 快取讀取
        article = self.redis_dao.get_article(self.user_id, self.article_id)
        if article:
            return article
        
        # 步驟 2: 快取未命中,從 MongoDB 讀取
        article = self.mongodb_dao.get_article(self.user_id, self.article_id)
        
        if article:
            # 步驟 3: 將資料寫入 Redis 快取
            self.redis_dao.save_article(article)
            return article
        
        # 步驟 4: 都找不到,拋出錯誤
        raise ArticleNotFoundError(self.article_id, self.user_id)

    def save(self, operation: str = "update", operation_desc: str = "Manual save"):
        """
        使用 Cache-Aside Pattern 儲存文章
        
        :raises DatabaseOperationError: 當儲存失敗時
        """
        success = self.mongodb_dao.save_article(self.article)
        if not success:
            raise DatabaseOperationError("save", "MongoDB", f"Article {self.article_id}")
        
        self.redis_dao.save_article(self.article)
        
        # 儲存版本
        if self.enable_versioning:
            self.version_manager.save_version(self.article, operation, operation_desc)
    
    def invalidate_cache(self):
        """手動清除 Redis 快取"""
        self.redis_dao.delete_article(self.user_id, self.article_id)
    
    def get_article_as_json(self) -> str:
        """以 JSON 字串形式獲取當前文章的內容。"""
        return self.article.model_dump_json(indent=2)
    
    def get_cache_info(self) -> dict:
        """取得快取資訊"""
        return self.redis_dao.get_cache_info(self.user_id, self.article_id)

    def undo(self) -> bool:
        """回到上一個版本"""
        if not self.enable_versioning:
            return False
        
        previous_article = self.version_manager.undo()
        if not previous_article:
            return False
        
        self.article = previous_article
        self.mongodb_dao.save_article(self.article)
        self.redis_dao.save_article(self.article)
        return True
    
    def redo(self) -> bool:
        """回到下一個版本"""
        if not self.enable_versioning:
            return False
        
        next_article = self.version_manager.redo()
        if not next_article:
            return False
        
        self.article = next_article
        self.mongodb_dao.save_article(self.article)
        self.redis_dao.save_article(self.article)
        return True
    
    def get_version_info(self) -> dict:
        """取得版本資訊"""
        if not self.enable_versioning:
            return {"versioning_enabled": False}
        
        return {
            "versioning_enabled": True,
            "current_version": self.version_manager.current_version_number,
            "max_version": self.version_manager.max_version_number,
            "can_undo": self.version_manager.can_undo(),
            "can_redo": self.version_manager.can_redo()
        }
    
    def update_article(self, updated_article: Article, operation_desc: str = "Updated entire article") -> str:
        """
        更新整個文章,包含所有 sections 和 content_blocks
        
        :param updated_article: 更新後的完整文章物件
        :param operation_desc: 操作描述
        :return: 成功訊息
        :raises ArticleNotFoundError: 當原文章不存在時
        :raises DatabaseOperationError: 當儲存失敗時
        """
        # 驗證文章 ID 和使用者 ID 是否匹配
        if updated_article.article_id != self.article_id:
            raise ValueError(f"Article ID mismatch: expected {self.article_id}, got {updated_article.article_id}")
        
        if updated_article.user_id != self.user_id:
            raise ValueError(f"User ID mismatch: expected {self.user_id}, got {updated_article.user_id}")
        
        # 更新內部文章物件
        self.article = updated_article
        
        # 儲存到資料庫和快取
        self.save(operation="update_article", operation_desc=operation_desc)
        
        return f"Success! Article '{self.article.title}' updated with {len(self.article.sections)} sections."


# --- 文章 CRUD 服務函式 ---

def create_new_article(user_id: str, title: str) -> str:
    """建立新文章,若標題重複則自動加上時間後綴"""
    mongodb_dao = get_article_dao()
    redis_dao = get_redis_article_dao(ttl=REDIS_CACHE_TTL)
    
    if not mongodb_dao:
        raise DatabaseConnectionError("MongoDB", "Connection not available")
    
    # 檢查使用者是否已有相同標題的文章
    existing_articles = mongodb_dao.get_user_article_ids(user_id)
    existing_titles = set()
    
    for article_id in existing_articles:
        try:
            article = mongodb_dao.get_article(user_id, article_id)
            if article:
                existing_titles.add(article.title)
        except Exception:
            continue
    
    # 如果標題重複,加上時間後綴
    final_title = title
    if title in existing_titles:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_title = f"{title}_{timestamp}"
    
    article_id = f"article-{uuid.uuid4().hex[:8]}"
    new_article = Article(article_id=article_id, user_id=user_id, title=final_title)
    
    success = mongodb_dao.save_article(new_article)
    if not success:
        raise DatabaseOperationError("create", "MongoDB", f"Article {article_id}")
    
    redis_dao.save_article(new_article)
    return article_id


def export_article_as_json(user_id: str, article_id: str) -> str:
    """將指定文件的完整內容匯出為 JSON 字串"""
    manager = ArticleManager(user_id, article_id)
    return manager.get_article_as_json()


def list_my_articles(user_id: str) -> List[ArticlesTitleResponse]:
    """列出使用者的所有文件"""
    mongodb_dao = get_article_dao()
    if not mongodb_dao:
        raise DatabaseConnectionError("MongoDB connection is not available.")

    article_ids = mongodb_dao.get_user_article_ids(user_id)

    if not article_ids:
        return []

    output = []
    for article_id in article_ids:
        try:
            manager = ArticleManager(user_id, article_id)
            response = ArticlesTitleResponse(
                articles_id=article_id,
                title=manager.article.title
            )
            output.append(response)
        except Exception as e:
            print(f"Warning: Article ID '{article_id}' could not be loaded: {e}")
            continue

    return output


def delete_article(user_id: str, article_id: str) -> str:
    """刪除整個文件(包含 MongoDB、Redis 和版本記錄)"""
    mongodb_dao = get_article_dao()
    redis_dao = get_redis_article_dao()
    version_dao = get_version_dao()
    
    if not mongodb_dao:
        raise DatabaseConnectionError("MongoDB connection is not available.")
    
    # 從 MongoDB 刪除文章
    success = mongodb_dao.delete_article(user_id, article_id)
    if not success:
        raise ArticleNotFoundError(f"Article '{article_id}' not found for user '{user_id}'.")
    
    # 從 Redis 快取刪除
    redis_dao.delete_article(user_id, article_id)
    
    # 刪除所有版本記錄
    deleted_versions = version_dao.delete_all_versions(user_id, article_id)
    
    return f"Success! Article '{article_id}' deleted (including {deleted_versions} version records)."


# --- 章節管理服務函式 ---

def add_main_section(user_id: str, article_id: str, title: str) -> tuple[str, str]:
    """新增一個頂層主章節到文件中"""
    manager = ArticleManager(user_id, article_id)
    new_section = Section(title=title, level=1)
    manager.article.sections.append(new_section)
    manager.save(operation="add_main_section", operation_desc=f"Added main section: {title}")
    return new_section.section_id, f"Success! New main section '{title}' created."


def add_subsection(user_id: str, article_id: str, parent_section_id: str, title: str) -> tuple[str, str]:
    """在現有章節中新增子章節"""
    manager = ArticleManager(user_id, article_id)
    parent = manager.article.find_section(parent_section_id)
    if not parent:
        raise SectionNotFoundError(f"Parent section with ID '{parent_section_id}' not found.")
    
    new_level = parent.level + 1
    new_section = Section(title=title, level=new_level)
    parent.subsections.append(new_section)
    
    manager.save(operation="add_subsection", operation_desc=f"Added subsection: {title}")
    return new_section.section_id, f"Success! New subsection '{title}' (Level: {new_level}) created under '{parent.title}' with ID '{new_section.section_id}'."


def delete_section(user_id: str, article_id: str, section_id: str) -> str:
    """刪除指定的章節及其所有子章節和內容"""
    manager = ArticleManager(user_id, article_id)
    
    # 檢查是否為頂層章節
    for i, sec in enumerate(manager.article.sections):
        if sec.section_id == section_id:
            deleted_title = sec.title
            manager.article.sections.pop(i)
            manager.save(operation="delete_section", operation_desc=f"Deleted section: {deleted_title}")
            return f"Success! Section '{deleted_title}' and all its content deleted."
    
    # 遞迴搜尋子章節
    def _find_and_delete(sections: List[Section]) -> bool:
        for parent in sections:
            for i, sub in enumerate(parent.subsections):
                if sub.section_id == section_id:
                    parent.subsections.pop(i)
                    return True
            if _find_and_delete(parent.subsections):
                return True
        return False
    
    if _find_and_delete(manager.article.sections):
        manager.save(operation="delete_subsection", operation_desc=f"Deleted subsection: {section_id}")
        return f"Success! Subsection deleted."
    
    raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")


# --- 內容區塊管理服務函式 ---

def add_content_block(user_id: str, article_id: str, section_id: str, text_content: str, type: str) -> tuple[str, str]:
    """在指定章節中新增段落文字"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    new_block = ContentBlock(type=type, content=text_content)
    section.content_blocks.append(new_block)
    manager.save(operation="add_paragraph", operation_desc=f"Added paragraph to section: {section.title}")
    return new_block.block_id, f"Success! Paragraph added to section '{section.title}'."


def delete_content_block(user_id: str, article_id: str, section_id: str, block_id: str) -> str:
    """刪除指定章節中的某個內容區塊"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    for i, block in enumerate(section.content_blocks):
        if block.block_id == block_id:
            block_type = block.type
            section.content_blocks.pop(i)
            manager.save(operation="delete_content_block", operation_desc=f"Deleted {block_type} from section: {section.title}")
            return f"Success! {block_type.capitalize()} block deleted from section '{section.title}'."
    
    raise ContentBlockNotFoundError(f"Content block with ID '{block_id}' not found in section '{section.title}'.")

def update_article_title(user_id: str, article_id: str, new_title: str) -> str:
    """
    更新文章標題
    
    :param user_id: 使用者 ID
    :param article_id: 文章 ID
    :param new_title: 新的文章標題
    :return: 成功訊息
    """
    manager = ArticleManager(user_id, article_id)
    old_title = manager.article.title
    manager.article.title = new_title
    manager.save(
        operation="update_article_title",
        operation_desc=f"Updated article title: {old_title} -> {new_title}"
    )
    return f"Success! Article title updated from '{old_title}' to '{new_title}'."

def update_article_prompt(user_id: str, article_id: str, new_prompt: str) -> str:
    """
    更新文章的生成提示詞
    
    :param user_id: 使用者 ID
    :param article_id: 文章 ID
    :param new_prompt: 新的提示詞
    :return: 成功訊息
    """
    manager = ArticleManager(user_id, article_id)
    old_prompt = manager.article.article_prompt
    manager.article.article_prompt = new_prompt
    manager.save(
        operation="update_article_prompt",
        operation_desc=f"Updated article prompt"
    )
    return f"Success! Article prompt updated."

def replace_section(
    user_id: str,
    article_id: str,
    section_id: str,
    updated_section: Section
) -> str:
    """替換整個章節,包含所有內容區塊和子章節"""
    manager = ArticleManager(user_id, article_id)
    
    # 驗證 section_id 是否匹配
    if updated_section.section_id != section_id:
        raise ValueError(f"Section ID mismatch: expected {section_id}, got {updated_section.section_id}")
    
    # 檢查是否為頂層章節
    for i, sec in enumerate(manager.article.sections):
        if sec.section_id == section_id:
            old_title = sec.title
            manager.article.sections[i] = updated_section
            manager.save(
                operation="replace_section",
                operation_desc=f"Replaced section: {old_title}"
            )
            return f"Success! Section '{old_title}' has been replaced."
        
        # 使用新的 replace_subsection 方法
        if sec.replace_subsection(section_id, updated_section):
            manager.save(
                operation="replace_subsection",
                operation_desc=f"Replaced subsection: {section_id}"
            )
            return f"Success! Subsection has been replaced."
    
    raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")

def copy_article_to_user(source_user_id: str, source_article_id: str, target_user_id: str) -> str:
    """
    複製文章給特定使用者,並自動共享所有參考的素材
    
    :param source_user_id: 來源使用者 ID
    :param source_article_id: 來源文章 ID
    :param target_user_id: 目標使用者 ID
    :return: 新文章的 ID
    :raises ArticleNotFoundError: 當來源文章不存在時
    :raises DatabaseOperationError: 當儲存失敗時
    """
    import copy
    from article_copilot.daos.mongo_db.material_dao import get_material_dao
    
    mongodb_dao = get_article_dao()
    redis_dao = get_redis_article_dao(ttl=REDIS_CACHE_TTL)
    material_dao = get_material_dao()
    
    if not mongodb_dao:
        raise DatabaseConnectionError("MongoDB", "Connection not available")
    
    # 載入來源文章
    source_article = mongodb_dao.get_article(source_user_id, source_article_id)
    if not source_article:
        raise ArticleNotFoundError(source_article_id, source_user_id)
    
    # 檢查目標使用者是否已有相同標題的文章
    target_articles = mongodb_dao.get_user_article_ids(target_user_id)
    existing_titles = set()
    
    for article_id in target_articles:
        try:
            article = mongodb_dao.get_article(target_user_id, article_id)
            if article:
                existing_titles.add(article.title)
        except Exception:
            continue
    
    # 如果標題重複,加上時間後綴
    final_title = source_article.title
    if source_article.title in existing_titles:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_title = f"{source_article.title}_{timestamp}"
    
    # 建立新的文章 ID
    new_article_id = f"article-{uuid.uuid4().hex[:8]}"
    
    # 深拷貝文章內容並更新 ID 和使用者
    new_article = copy.deepcopy(source_article)
    new_article.article_id = new_article_id
    new_article.user_id = target_user_id
    new_article.title = final_title
    
    # 收集所有參考的素材 ID
    referenced_material_ids = set()
    
    def collect_material_ids(sections):
        """遞迴收集所有 section 和 content_block 中的 reference_material_ids"""
        for section in sections:
            # 收集該 section 的所有 content_blocks 中的素材 ID
            for block in section.content_blocks:
                if hasattr(block, 'reference_material_ids') and block.reference_material_ids:
                    referenced_material_ids.update(block.reference_material_ids)
            
            # 遞迴處理子章節
            if section.subsections:
                collect_material_ids(section.subsections)
    
    # 收集文章中所有參考的素材 ID
    collect_material_ids(new_article.sections)
    
    # 將目標使用者加入所有參考素材的共享列表
    shared_count = 0
    for material_id in referenced_material_ids:
        try:
            # 檢查素材是否存在
            material = material_dao.get_material(material_id)
            if material:
                # 只有當目標使用者不是素材擁有者時才需要加入共享列表
                if material.user_id != target_user_id:
                    success = material_dao.share_material_with_users(material_id, [target_user_id])
                    if success:
                        shared_count += 1
        except Exception as e:
            # 記錄錯誤但不中斷複製流程
            print(f"Warning: Failed to share material {material_id}: {e}")
            continue
    
    # 儲存新文章到 MongoDB
    success = mongodb_dao.save_article(new_article)
    if not success:
        raise DatabaseOperationError("copy", "MongoDB", f"Article {new_article_id}")
    
    # 儲存到 Redis 快取
    redis_dao.save_article(new_article)
    
    print(f"Article copied. Shared {shared_count} materials with user {target_user_id}")
    
    return new_article_id
