"""Article Manager Service - 文章管理服務層"""
import uuid
from typing import Any, Dict, List

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


# --- 文章 CRUD 服務函式 ---

def create_new_article(user_id: str, title: str) -> str:
    """建立新文章"""
    mongodb_dao = get_article_dao()
    redis_dao = get_redis_article_dao(ttl=REDIS_CACHE_TTL)
    
    if not mongodb_dao:
        raise DatabaseConnectionError("MongoDB", "Connection not available")
        
    article_id = f"article-{uuid.uuid4().hex[:8]}"
    new_article = Article(article_id=article_id, user_id=user_id, title=title)
    
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

def list_sections(user_id: str, article_id: str) -> Dict[str, Any]:
    """列出文件的完整層級結構"""
    manager = ArticleManager(user_id, article_id)
    
    def _section_to_dict(section: Section) -> Dict[str, Any]:
        """將 Section 轉換為字典格式"""
        return {
            "section_id": section.section_id,
            "title": section.title,
            "level": section.level,
            "content_blocks": [
                {
                    "block_id": block.block_id,
                    "type": block.type,
                    "content_preview": str(block.content)[:50] + "..." if len(str(block.content)) > 100 else str(block.content)
                }
                for block in section.content_blocks
            ],
            "subsections": [_section_to_dict(sub) for sub in section.subsections]
        }
    
    return {
        "article_id": manager.article.article_id,
        "article_title": manager.article.title,
        "user_id": manager.article.user_id,
        "total_sections": len(manager.article.sections),
        "sections": [_section_to_dict(sec) for sec in manager.article.sections]
    }


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


def update_section_title(user_id: str, article_id: str, section_id: str, new_title: str) -> str:
    """更新指定章節的標題"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    old_title = section.title
    section.title = new_title
    manager.save(operation="update_section_title", operation_desc=f"Updated section title: {old_title} -> {new_title}")
    return f"Success! Section title updated from '{old_title}' to '{new_title}'."


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

def add_paragraph(user_id: str, article_id: str, section_id: str, text_content: str) -> tuple[str, str]:
    """在指定章節中新增段落文字"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    new_block = ContentBlock(type="paragraph", content=text_content)
    section.content_blocks.append(new_block)
    manager.save(operation="add_paragraph", operation_desc=f"Added paragraph to section: {section.title}")
    return new_block.block_id, f"Success! Paragraph added to section '{section.title}'."


def update_paragraph(user_id: str, article_id: str, section_id: str, block_id: str, new_text: str) -> str:
    """更新指定章節中某個段落的內容"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    block = next((b for b in section.content_blocks if b.block_id == block_id), None)
    if not block:
        raise ContentBlockNotFoundError(f"Content block with ID '{block_id}' not found in section '{section.title}'.")
    
    if block.type != "paragraph":
        raise InvalidContentTypeError(f"Block '{block_id}' is not a paragraph (type: {block.type}).")
    
    block.content = new_text
    manager.save(operation="update_paragraph", operation_desc=f"Updated paragraph in section: {section.title}")
    return f"Success! Paragraph in section '{section.title}' updated."


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


# --- LangChain 工具工廠 (給 Agent 使用) ---

def get_article_editing_tools(user_id: str, article_id: str) -> list:
    """工廠函式:建立並回傳文件編輯工具列表 (僅包含文章和章節管理)"""

    @tool
    def list_sections_tool() -> str:
        """Lists the complete hierarchical structure of the current article."""
        try:
            return str(list_sections(user_id, article_id))
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def add_main_section_tool(title: str) -> str:
        """Adds a new TOP-LEVEL main section to the article."""
        try:
            section_id, message = add_main_section(user_id, article_id, title)
            return message
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def add_subsection_tool(parent_section_id: str, title: str) -> str:
        """Adds a subsection within an existing section."""
        try:
            section_id, message = add_subsection(user_id, article_id, parent_section_id, title)
            return message
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def add_paragraph_tool(section_id: str, text_content: str) -> str:
        """Adds a block of text (a paragraph) to a specific section."""
        try:
            block_id, message = add_paragraph(user_id, article_id, section_id, text_content)
            return message
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def update_section_title_tool(section_id: str, new_title: str) -> str:
        """Updates the title of an existing section."""
        try:
            return update_section_title(user_id, article_id, section_id, new_title)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def update_paragraph_tool(section_id: str, block_id: str, new_text: str) -> str:
        """Updates the content of an existing paragraph."""
        try:
            return update_paragraph(user_id, article_id, section_id, block_id, new_text)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def delete_section_tool(section_id: str) -> str:
        """Deletes a section and all its subsections."""
        try:
            return delete_section(user_id, article_id, section_id)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def delete_content_block_tool(section_id: str, block_id: str) -> str:
        """Deletes a specific content block from a section."""
        try:
            return delete_content_block(user_id, article_id, section_id, block_id)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def list_my_articles_tool() -> str:
        """Lists all articles belonging to the current user."""
        try:
            articles = list_my_articles(user_id)
            if not articles:
                return f"No articles found for user '{user_id}'."
            
            output = f"Articles for user '{user_id}':\n"
            for article in articles:
                output += f"- {article.title} (ID: {article.articles_id})\n"
            return output
        except Exception as e:
            return f"Error: {str(e)}"

    return [
        list_my_articles_tool,
        list_sections_tool,
        add_main_section_tool,
        add_subsection_tool,
        add_paragraph_tool,
        update_section_title_tool,
        update_paragraph_tool,
        delete_section_tool,
        delete_content_block_tool,
    ]