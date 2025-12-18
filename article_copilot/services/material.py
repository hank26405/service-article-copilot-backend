from fastapi import UploadFile
from typing import List, Optional
from datetime import datetime
import re
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

    def _generate_material_id(self) -> str:
        """生成素材 ID (純 UUID)"""
        return f"mat-{uuid.uuid4().hex[:12]}"

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

        # 如果檔名重複,加上時間後綴
        if self.material_dao.check_filename_exists(self.user_id, filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                filename = f"{filename}_{timestamp}"

        new_material_id = self._generate_material_id()

        # 1. 存入 GridFS (原始檔)
        gridfs_id = self.material_dao.save_file_to_gridfs(content, filename, content_type)

        # 2. ETL 處理 (解析內容)
        try:
            processor = FileProcessorFactory.get_processor(content_type)
            display_data, llm_context, page_count = processor.process(content, filename)
        except ValueError:
            display_data = f"Unsupported preview for {content_type}"
            llm_context = f"File: {filename} (Unsupported format for text extraction)"
            page_count = 1

        # 3. 處理需要動態 URL 的情況
        if display_data == "__API_URL_PLACEHOLDER__":
            display_data = {"type": "api_view", "url_template": f"/api/materials/{new_material_id}/view"}
        
        if display_data == ["__SLIDE_IMAGES_PLACEHOLDER__"]:
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

    async def process_paste_content(self, html_content: str, filename: str = None) -> Material:
        """
        處理 Excel/網頁 貼上 (Pure HTML String)
        """
        # 1. 準備偽造的檔案資訊
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"Pasted_Table_{timestamp}.html"
        
        # 如果檔名重複,加上時間後綴
        if self.material_dao.check_filename_exists(self.user_id, filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                filename = f"{filename}_{timestamp}"
    
        content_type = "text/html"
        # 轉成 bytes,因為我們的 GridFS 和 Processor 都吃 bytes
        content_bytes = html_content.encode('utf-8')
        file_size = len(content_bytes)

        # 3. 存入 GridFS (作為備份,雖然是貼上的,但存下來以防萬一)
        gridfs_id = self.material_dao.save_file_to_gridfs(content_bytes, filename, content_type)
        new_material_id = self._generate_material_id()

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
            
            # 對於貼上的表格,Display Data 直接是 HTML 字串,
            # 前端收到後會直接 render,不需要 URL
            display_data=display_data, 
            
            llm_context=llm_context,
            page_count=page_count
        )

        success = self.material_dao.save_material(material)
        if not success:
            raise Exception("Failed to save pasted material")
            
        return material

    async def process_text_content(self, text_content: str, filename: str = None, content_type: str = "text/plain") -> Material:
        """
        處理純文字或 JSON 字串上傳
        """
        # 1. 準備檔案資訊
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            extension = "json" if content_type == "application/json" else "txt"
            filename = f"Text_{timestamp}.{extension}"
        
        # 如果檔名重複,加上時間後綴
        if self.material_dao.check_filename_exists(self.user_id, filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                filename = f"{filename}_{timestamp}"
    
        # 轉成 bytes
        content_bytes = text_content.encode('utf-8')
        file_size = len(content_bytes)
        new_material_id = self._generate_material_id()

        # 2. 存入 GridFS
        gridfs_id = self.material_dao.save_file_to_gridfs(content_bytes, filename, content_type)

        # 3. ETL 處理
        try:
            processor = FileProcessorFactory.get_processor(content_type)
            display_data, llm_context, page_count = processor.process(content_bytes, filename)
        except ValueError:
            # 如果沒有對應的 processor,直接使用原始文字
            display_data = text_content
            llm_context = f"File: {filename}\nContent:\n{text_content}"
            page_count = 1

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
            raise Exception("Failed to save text material")
            
        return material

    def update_material_filename(self, material_id: str, new_filename: str) -> Material:
        """
        更新素材檔名
        
        :param material_id: 素材 ID
        :param new_filename: 新的檔名
        :return: 更新後的素材物件
        :raises ValueError: 當使用者無權限或素材不存在時
        """
        # 檢查是否為擁有者
        material = self.material_dao.get_material(material_id)
        if not material or material.user_id != self.user_id:
            raise ValueError("Not authorized or material not found")
        
        # 如果新檔名與原檔名相同,直接返回
        if material.filename == new_filename:
            return material
        
        # 檢查新檔名是否與其他素材重複
        if self.material_dao.check_filename_exists(self.user_id, new_filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = new_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                new_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                new_filename = f"{new_filename}_{timestamp}"
        
        # 更新檔名
        material.filename = new_filename
        success = self.material_dao.save_material(material)
        
        if not success:
            raise Exception("Failed to update material filename")
        
        return material
