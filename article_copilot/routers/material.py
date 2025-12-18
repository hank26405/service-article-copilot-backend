"""This file creates the FastAPI router for material-related endpoints."""
from article_copilot.exceptions.article_exceptions import ContentBlockNotFoundError, SectionNotFoundError
from article_copilot.models.domain.user import User
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io
from pydantic import BaseModel
from urllib.parse import quote

from article_copilot.models.api.requests.material_requests import PasteRequest, TextUploadRequest


from article_copilot.models.domain.material import Material
from article_copilot.services.material import MaterialService
from article_copilot.security.auth import get_current_user


def create_material_router() -> APIRouter:

    router = APIRouter()

    @router.post("/upload", response_model=Material)
    async def upload_material(
        file: UploadFile = File(...), 
        current_user: User = Depends(get_current_user)
    ):
        """上傳檔案並建立素材"""
        service = MaterialService(current_user.id)
        try:
            material = await service.process_upload(file)
            return material
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @router.post("/paste", response_model=Material)
    async def paste_material(
        request: PasteRequest,
        current_user: User = Depends(get_current_user)
    ):
        """
        處理剪貼簿貼上 (Excel/HTML) 並建立素材
        前端需傳送包含 html_content 的 JSON
        """
        service = MaterialService(current_user.id)
        try:
            material = await service.process_paste_content(request.html_content, request.filename)
            return material
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Paste processing failed: {str(e)}")

    @router.post("/upload-text", response_model=Material)
    async def upload_text_material(
        request: TextUploadRequest,
        current_user: User = Depends(get_current_user)
    ):
        """
        上傳純文字或 JSON 字串並建立素材
        前端需傳送包含 text_content 的 JSON
        """
        service = MaterialService(current_user.id)
        try:
            material = await service.process_text_content(
                request.text_content, 
                request.filename,
                request.content_type
            )
            return material
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Text upload failed: {str(e)}")


    @router.get("/list/own", response_model=List[Material])
    async def list_own_materials(current_user: User = Depends(get_current_user)):
        """列出使用者自己擁有的所有素材"""
        service = MaterialService(current_user.id)
        return service.list_own_materials()

    @router.get("/list/shared", response_model=List[Material])
    async def list_shared_materials(current_user: User = Depends(get_current_user)):
        """列出別人分享給使用者的所有素材"""
        service = MaterialService(current_user.id)
        return service.list_shared_materials()

    @router.get("/list/all", response_model=List[Material])
    async def list_all_accessible_materials(current_user: User = Depends(get_current_user)):
        """列出所有可存取的素材 (自己的 + 被分享的)"""
        service = MaterialService(current_user.id)
        return service.list_all_accessible_materials()

    @router.post("/{material_id}/share")
    async def share_material(
        material_id: str,
        target_user_ids: List[str],
        current_user: User = Depends(get_current_user)
    ):
        """分享素材給其他使用者"""
        service = MaterialService(current_user.id)
        success = service.share_material(material_id, target_user_ids)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material shared successfully", "shared_with": target_user_ids}

    @router.post("/{material_id}/unshare")
    async def unshare_material(
        material_id: str,
        target_user_ids: List[str],
        current_user: User = Depends(get_current_user)
    ):
        """取消分享素材給指定使用者"""
        service = MaterialService(current_user.id)
        success = service.unshare_material(material_id, target_user_ids)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material unshared successfully", "unshared_from": target_user_ids}

    @router.delete("/{material_id}")
    async def delete_material(
        material_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """刪除素材 (僅擁有者可刪除)"""
        service = MaterialService(current_user.id)
        success = service.delete_material(material_id)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material deleted successfully"}

    @router.get("/{material_id}", response_model=Material)
    async def get_material_info(material_id: str, current_user: User = Depends(get_current_user)):
        """取得素材 Metadata"""
        service = MaterialService(current_user.id)
        material = service.get_material(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        return material

    @router.get("/{material_id}/view")
    async def view_material_file(material_id: str, current_user: User = Depends(get_current_user)):
        """
        取得原始檔案內容 (Stream)
        適用於顯示 PDF 或 Image
        """
        service = MaterialService(current_user.id)
        material = service.get_material(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # 檢查權限
        if material.user_id != current_user.id and current_user.id not in material.shared_with_users:
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_bytes = service.get_file_content(material_id)
        if not file_bytes:
            raise HTTPException(status_code=404, detail="File content not found")
        
        # URL 編碼檔名以支援中文
        encoded_filename = quote(material.filename)
        
        return StreamingResponse(
            io.BytesIO(file_bytes), 
            media_type=material.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )

    @router.patch("/{material_id}/filename")
    async def update_material_filename(
        material_id: str,
        new_filename: str,
        current_user: User = Depends(get_current_user)
    ):
        """更新素材檔名 (僅擁有者可修改)"""
        service = MaterialService(current_user.id)
        try:
            material = service.update_material_filename(material_id, new_filename)
            return {
                "message": "Filename updated successfully",
                "material_id": material.material_id,
                "new_filename": material.filename
            }
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

    return router