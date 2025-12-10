"""Prompt Manager Service - 提示詞管理服務層"""
from article_copilot.services.article_manager import ArticleManager
from article_copilot.exceptions import (
    SectionNotFoundError,
    ContentBlockNotFoundError,
)


def update_article_prompt(user_id: str, article_id: str, new_prompt: str) -> str:
    """更新文章層級的提示詞"""
    manager = ArticleManager(user_id, article_id)
    old_prompt = manager.article.article_prompt
    manager.article.article_prompt = new_prompt
    manager.save(operation="update_article_prompt", operation_desc="Updated article prompt")
    return f"Success! Article prompt updated from '{old_prompt}' to '{new_prompt}'."


def update_section_prompt(user_id: str, article_id: str, section_id: str, new_prompt: str) -> str:
    """更新章節層級的提示詞"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    old_prompt = section.section_prompt
    section.section_prompt = new_prompt
    manager.save(operation="update_section_prompt", operation_desc=f"Updated section '{section.title}' prompt")
    return f"Success! Section '{section.title}' prompt updated from '{old_prompt}' to '{new_prompt}'."


def update_content_block_prompt(user_id: str, article_id: str, section_id: str, block_id: str, new_prompt: str) -> str:
    """更新內容區塊層級的提示詞"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    block = next((b for b in section.content_blocks if b.block_id == block_id), None)
    if not block:
        raise ContentBlockNotFoundError(f"Content block with ID '{block_id}' not found in section '{section.title}'.")
    
    old_prompt = block.block_prompt
    block.block_prompt = new_prompt
    manager.save(operation="update_block_prompt", operation_desc=f"Updated block prompt in section '{section.title}'")
    return f"Success! Content block prompt in section '{section.title}' updated from '{old_prompt}' to '{new_prompt}'."


def toggle_article_fixed(user_id: str, article_id: str) -> str:
    """切換文章的固定狀態"""
    manager = ArticleManager(user_id, article_id)
    manager.article.fixed = not manager.article.fixed
    status = "fixed" if manager.article.fixed else "unfixed"
    manager.save(operation="toggle_article_fixed", operation_desc=f"Article {status}")
    return f"Success! Article '{manager.article.title}' is now {status}."


def toggle_section_fixed(user_id: str, article_id: str, section_id: str) -> str:
    """切換章節的固定狀態"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    section.fixed = not section.fixed
    status = "fixed" if section.fixed else "unfixed"
    manager.save(operation="toggle_section_fixed", operation_desc=f"Section '{section.title}' {status}")
    return f"Success! Section '{section.title}' is now {status}."


def toggle_content_block_fixed(user_id: str, article_id: str, section_id: str, block_id: str) -> str:
    """切換內容區塊的固定狀態"""
    manager = ArticleManager(user_id, article_id)
    section = manager.article.find_section(section_id)
    if not section:
        raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
    
    block = next((b for b in section.content_blocks if b.block_id == block_id), None)
    if not block:
        raise ContentBlockNotFoundError(f"Content block with ID '{block_id}' not found in section '{section.title}'.")
    
    block.fixed = not block.fixed
    status = "fixed" if block.fixed else "unfixed"
    manager.save(operation="toggle_block_fixed", operation_desc=f"Block in '{section.title}' {status}")
    return f"Success! Content block in section '{section.title}' is now {status}."