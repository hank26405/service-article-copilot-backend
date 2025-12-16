"""This file creates the FastAPI router for material-related endpoints."""
from article_copilot.exceptions.article_exceptions import ContentBlockNotFoundError, SectionNotFoundError
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io

from article_copilot.models.api.requests.material_requests import PasteRequest
from article_copilot.models.domain.material import Material
from article_copilot.services.material import MaterialService
from article_copilot.security.auth import get_current_user


def create_material_router() -> APIRouter:

    router = APIRouter()

    @router.post("/upload", response_model=Material)
    async def upload_material(
        file: UploadFile = File(...), 
        user_id: str = Depends(get_current_user)
    ):
        """上傳檔案並建立素材"""
        service = MaterialService(user_id)
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
        user_id: str = Depends(get_current_user)
    ):
        """
        處理剪貼簿貼上 (Excel/HTML) 並建立素材
        前端需傳送包含 html_content 的 JSON
        """
        service = MaterialService(user_id)
        try:
            material = await service.process_paste_content(request.html_content)
            return material
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Paste processing failed: {str(e)}")

    @router.get("/list", response_model=List[Material])
    async def list_materials(
        include_shared: bool = False,
        user_id: str = Depends(get_current_user)
    ):
        """
        列出素材
        :param include_shared: 是否包含被分享的素材
        """
        service = MaterialService(user_id)
        return service.list_materials(include_shared=include_shared)

    @router.get("/list/own", response_model=List[Material])
    async def list_own_materials(user_id: str = Depends(get_current_user)):
        """列出使用者自己擁有的所有素材"""
        service = MaterialService(user_id)
        return service.list_own_materials()

    @router.get("/list/shared", response_model=List[Material])
    async def list_shared_materials(user_id: str = Depends(get_current_user)):
        """列出別人分享給使用者的所有素材"""
        service = MaterialService(user_id)
        return service.list_shared_materials()

    @router.get("/list/all", response_model=List[Material])
    async def list_all_accessible_materials(user_id: str = Depends(get_current_user)):
        """列出所有可存取的素材 (自己的 + 被分享的)"""
        service = MaterialService(user_id)
        return service.list_all_accessible_materials()

    @router.post("/{material_id}/share")
    async def share_material(
        material_id: str,
        target_user_ids: List[str],
        user_id: str = Depends(get_current_user)
    ):
        """分享素材給其他使用者"""
        service = MaterialService(user_id)
        success = service.share_material(material_id, target_user_ids)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material shared successfully", "shared_with": target_user_ids}

    @router.post("/{material_id}/unshare")
    async def unshare_material(
        material_id: str,
        target_user_ids: List[str],
        user_id: str = Depends(get_current_user)
    ):
        """取消分享素材給指定使用者"""
        service = MaterialService(user_id)
        success = service.unshare_material(material_id, target_user_ids)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material unshared successfully", "unshared_from": target_user_ids}

    @router.delete("/{material_id}")
    async def delete_material(
        material_id: str,
        user_id: str = Depends(get_current_user)
    ):
        """刪除素材 (僅擁有者可刪除)"""
        service = MaterialService(user_id)
        success = service.delete_material(material_id)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or material not found")
        return {"message": "Material deleted successfully"}

    @router.get("/{material_id}", response_model=Material)
    async def get_material_info(material_id: str, user_id: str = Depends(get_current_user)):
        """取得素材 Metadata"""
        service = MaterialService(user_id)
        material = service.get_material(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        return material

    @router.get("/{material_id}/view")
    async def view_material_file(material_id: str, user_id: str = Depends(get_current_user)):
        """
        取得原始檔案內容 (Stream)
        適用於顯示 PDF 或 Image
        """
        service = MaterialService(user_id)
        material = service.get_material(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        file_bytes = service.get_file_content(material_id)
        if not file_bytes:
            raise HTTPException(status_code=404, detail="File content not found")
        
        return StreamingResponse(
            io.BytesIO(file_bytes), 
            media_type=material.mime_type,
            headers={"Content-Disposition": f"inline; filename={material.filename}"}
        )

    @router.post("/references/article/{article_id}")
    async def update_article_references(
        article_id: str,
        material_names: List[str],
        user_id: str = Depends(get_current_user)
    ):
        """更新文章層級的參考素材名稱列表"""
        service = MaterialService(user_id)
        try:
            success = service.update_article_references(article_id, material_names)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update article references")
            return {
                "message": "Article references updated successfully",
                "article_id": article_id,
                "material_names": material_names
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/references/section/{article_id}/{section_id}")
    async def update_section_references(
        article_id: str,
        section_id: str,
        material_names: List[str],
        user_id: str = Depends(get_current_user)
    ):
        """更新章節層級的參考素材名稱列表"""
        service = MaterialService(user_id)
        try:
            success = service.update_section_references(article_id, section_id, material_names)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update section references")
            return {
                "message": "Section references updated successfully",
                "article_id": article_id,
                "section_id": section_id,
                "material_names": material_names
            }
        except SectionNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/references/block/{article_id}/{section_id}/{block_id}")
    async def update_block_references(
        article_id: str,
        section_id: str,
        block_id: str,
        material_names: List[str],
        user_id: str = Depends(get_current_user)
    ):
        """更新內容區塊層級的參考素材名稱列表"""
        service = MaterialService(user_id)
        try:
            success = service.update_block_references(article_id, section_id, block_id, material_names)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update block references")
            return {
                "message": "Block references updated successfully",
                "article_id": article_id,
                "section_id": section_id,
                "block_id": block_id,
                "material_names": material_names
            }
        except (SectionNotFoundError, ContentBlockNotFoundError) as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router