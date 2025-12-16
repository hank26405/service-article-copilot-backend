from fastapi import UploadFile
from typing import List, Optional
from datetime import datetime
import uuid
from article_copilot.models.domain.material import Material
from article_copilot.daos.mongo_db.material_dao import get_material_dao
from article_copilot.services.file_processor import FileProcessorFactory
from article_copilot.services.article_manager import ArticleManager
from article_copilot.exceptions import SectionNotFoundError, ContentBlockNotFoundError

class MaterialService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.material_dao = get_material_dao()

    async def process_upload(self, file: UploadFile) -> Material:
        """
        處理檔案上傳: 
        1. 讀取 -> GridFS
        2. Processor -> Display/LLM View
        3. Save Metadata
        """
        content = await file.read()
        filename = file.filename
        content_type = file.content_type
        file_size = len(content)

        # 1. 存入 GridFS (原始檔)
        gridfs_id = self.material_dao.save_file_to_gridfs(content, filename, content_type)

        # 2. ETL 處理 (解析內容)
        try:
            processor = FileProcessorFactory.get_processor(content_type)
            display_data, llm_context, page_count = processor.process(content, filename)
        except ValueError:
            # 遇到不支援的格式，做最基本的處理
            display_data = f"Unsupported preview for {content_type}"
            llm_context = f"File: {filename} (Unsupported format for text extraction)"
            page_count = 1

        # 3. 修正 Display Data 路徑
        # 如果 Processor 回傳的是 Placeholder，我們替換成正確的 API URL
        new_material_id = f"mat-{uuid.uuid4().hex[:8]}"
        
        # 稍後建立 Material 物件後才有 ID，這裡先不處理 URL 的動態 ID
        # 改為在 Router 回傳或前端使用時，前端知道如何組裝 URL: /api/materials/{id}/view
        
        if display_data == "__API_URL_PLACEHOLDER__":
            # 標記為需要前端動態載入的類型
            display_data = {"type": "api_view", "url_template": f"/api/materials/{new_material_id}/view"}
        
        if display_data == ["__SLIDE_IMAGES_PLACEHOLDER__"]:
             # PPT 情況: 這裡簡化，實際應在 Processor 中生成圖片並存回 GridFS
             # 這裡我們回傳一個標記，前端顯示預設圖示
             display_data = {"type": "slides", "count": page_count, "note": "Slide preview requires rendering server"}

        # 4. 建立 Material 物件
        material = Material(
            material_id=new_material_id,
            user_id=self.user_id,
            filename=filename,
            mime_type=content_type,
            gridfs_id=gridfs_id,
            file_size=file_size,
            display_data=display_data,
            llm_context=llm_context,
            page_count=page_count
        )

        success = self.material_dao.save_material(material)
        if not success:
            raise Exception("Failed to save material metadata")
            
        return material

    def list_materials(self, include_shared: bool = False) -> List[Material]:
        """
        列出素材
        
        :param include_shared: 是否包含被分享的素材
        :return: 素材列表
        """
        if include_shared:
            return self.material_dao.list_all_accessible_materials(self.user_id)
        else:
            return self.material_dao.list_user_materials(self.user_id)

    def list_own_materials(self) -> List[Material]:
        """列出使用者自己擁有的所有素材"""
        return self.material_dao.list_user_materials(self.user_id)

    def list_shared_materials(self) -> List[Material]:
        """列出別人分享給使用者的所有素材"""
        return self.material_dao.list_shared_materials(self.user_id)

    def list_all_accessible_materials(self) -> List[Material]:
        """列出所有可存取的素材 (自己的 + 被分享的)"""
        return self.material_dao.list_all_accessible_materials(self.user_id)

    def share_material(self, material_id: str, target_user_ids: List[str]) -> bool:
        """
        分享素材給其他使用者
        
        :param material_id: 素材 ID
        :param target_user_ids: 目標使用者 ID 列表
        :return: 是否分享成功
        """
        # 檢查是否為擁有者
        material = self.material_dao.get_material(material_id)
        if not material or material.user_id != self.user_id:
            return False
        
        return self.material_dao.share_material_with_users(material_id, target_user_ids)

    def unshare_material(self, material_id: str, target_user_ids: List[str]) -> bool:
        """
        取消分享素材給指定使用者
        
        :param material_id: 素材 ID
        :param target_user_ids: 目標使用者 ID 列表
        :return: 是否取消成功
        """
        # 檢查是否為擁有者
        material = self.material_dao.get_material(material_id)
        if not material or material.user_id != self.user_id:
            return False
        
        return self.material_dao.unshare_material_with_users(material_id, target_user_ids)

    def delete_material(self, material_id: str) -> bool:
        """
        刪除素材 (僅擁有者可刪除)
        
        :param material_id: 素材 ID
        :return: 是否刪除成功
        """
        # 檢查是否為擁有者
        material = self.material_dao.get_material(material_id)
        if not material or material.user_id != self.user_id:
            return False
        
        return self.material_dao.delete_material_completely(material_id)

    def get_material(self, material_id: str) -> Optional[Material]:
            """取得素材 Metadata，並檢查存取權限"""
            
            # 1. 取得素材
            material = self.material_dao.get_material(material_id)
            if not material:
                return None
            
            # 2. 檢查存取權限 (self.user_id 是當前登入者)
            # 優先檢查：擁有者
            if material.user_id == self.user_id:
                return material
                
            # 最後檢查：是否明確共享給當前使用者
            if self.user_id in material.shared_with_users:
                return material

            # 不滿足任何條件
            return None
    
    def get_material_by_name(self, filename: str) -> Optional[Material]:
        materials = self.material_dao.list_user_materials(self.user_id)
        for material in materials:
            if material.filename == filename:
                return material
        return None

    def get_file_content(self, material_id: str) -> Optional[bytes]:
        """取得原始檔案內容 (Binary)"""
        material = self.get_material(material_id)
        if not material:
            return None
        return self.material_dao.get_file_from_gridfs(material.gridfs_id)

    async def process_paste_content(self, html_content: str) -> Material:
        """
        處理 Excel/網頁 貼上 (Pure HTML String)
        """
        # 1. 準備偽造的檔案資訊
        # 因為來源是字串，我們自己定義一個檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Pasted_Table_{timestamp}.html"
        content_type = "text/html"
        
        # 轉成 bytes，因為我們的 GridFS 和 Processor 都吃 bytes
        content_bytes = html_content.encode('utf-8')
        file_size = len(content_bytes)

        new_material_id = f"mat-{uuid.uuid4().hex[:8]}"

        # 3. 存入 GridFS (作為備份，雖然是貼上的，但存下來以防萬一)
        gridfs_id = self.material_dao.save_file_to_gridfs(content_bytes, filename, content_type)

        # 4. ETL 處理
        try:
            # 這裡我們明確呼叫 HTML 處理器
            processor = FileProcessorFactory.get_processor("text/html")
            display_data, llm_context, page_count = processor.process(content_bytes, filename)
        except Exception as e:
            display_data = f"<div>Error processing paste: {e}</div>"
            llm_context = f"Error: {e}"
            page_count = 1

        # 5. 建立 Material 物件
        material = Material(
            material_id=new_material_id,
            user_id=self.user_id,
            filename=filename,
            mime_type=content_type,
            gridfs_id=gridfs_id,
            file_size=file_size,
            
            # 對於貼上的表格，Display Data 直接是 HTML 字串，
            # 前端收到後會直接 render，不需要 URL
            display_data=display_data, 
            
            llm_context=llm_context,
            page_count=page_count
        )

        success = self.material_dao.save_material(material)
        if not success:
            raise Exception("Failed to save pasted material")
            
        return material

    def update_article_references(self, article_id: str, material_names: List[str]) -> bool:
        """
        更新文章層級的參考素材名稱列表
        
        :param article_id: 文章 ID
        :param material_names: 素材名稱列表
        :return: 是否更新成功
        """
        
        manager = ArticleManager(self.user_id, article_id)
        manager.article.reference_material_names = material_names
        manager.save(
            operation="update_article_references",
            operation_desc=f"Updated article references: {', '.join(material_names)}"
        )
        return True

    def update_section_references(self, article_id: str, section_id: str, material_names: List[str]) -> bool:
        """
        更新章節層級的參考素材名稱列表
        
        :param article_id: 文章 ID
        :param section_id: 章節 ID
        :param material_names: 素材名稱列表
        :return: 是否更新成功
        """
        
        manager = ArticleManager(self.user_id, article_id)
        section = manager.article.find_section(section_id)
        
        if not section:
            raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
        
        section.reference_material_names = material_names
        manager.save(
            operation="update_section_references",
            operation_desc=f"Updated section '{section.title}' references: {', '.join(material_names)}"
        )
        return True

    def update_block_references(self, article_id: str, section_id: str, block_id: str, material_names: List[str]) -> bool:
        """
        更新內容區塊層級的參考素材名稱列表
        
        :param article_id: 文章 ID
        :param section_id: 章節 ID
        :param block_id: 內容區塊 ID
        :param material_names: 素材名稱列表
        :return: 是否更新成功
        """
        
        manager = ArticleManager(self.user_id, article_id)
        section = manager.article.find_section(section_id)
        
        if not section:
            raise SectionNotFoundError(f"Section with ID '{section_id}' not found.")
        
        block = next((b for b in section.content_blocks if b.block_id == block_id), None)
        if not block:
            raise ContentBlockNotFoundError(f"Content block with ID '{block_id}' not found.")
        
        block.reference_material_names = material_names
        manager.save(
            operation="update_block_references",
            operation_desc=f"Updated block '{block_id}' references in section '{section.title}': {', '.join(material_names)}"
        )
        return True
