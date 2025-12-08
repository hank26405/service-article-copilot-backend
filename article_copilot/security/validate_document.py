# ems_llm/security/validate_document.py
import os
import magic
from fastapi import UploadFile, File, HTTPException, Request, status

# --- 安全配置 ---
# 白名單：只允許這些副檔名
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".md", ".docx", ".doc"}
# 白名單：只允許這些真實的 MIME 類型 (從檔案內容判斷)
ALLOWED_MIME_TYPES = {
    "text/plain", 
    "application/pdf", 
    "application/msword",  # for .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # for .docx
}
# 檔案大小限制 (Bytes)，例如 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024

def _sanitize_filename(filename: str) -> str:
    """
    對檔名進行清理，防止路徑遍歷。
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot be empty."
        )
    basename = os.path.basename(filename)
    if ".." in basename or "/" in basename or "\\" in basename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name contains invalid characters."
        )
    return basename

async def validate_document(
    request: Request, 
    file: UploadFile = File(...)
) -> tuple[bytes, str]:
    """
    一個 FastAPI 依賴項，用於在上傳時驗證文件。
    驗證成功後，返回文件的內容 (bytes) 和清理過的檔名。
    """
    # 1. 檢查檔名和副檔名
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is missing."
        )
    safe_filename = _sanitize_filename(file.filename)
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension. Allowed are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. 讀取檔案內容並檢查大小
    # 這是最可靠的方法，因為 Content-Length 有可能被偽造或省略
    file_contents = await file.read()
    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the limit of {MAX_FILE_SIZE / 1024 / 1024} MB."
        )
        
    # 重置文件指標，以防萬一其他地方需要再次讀取 (雖然這裡我們直接回傳內容)
    await file.seek(0)

    # 3. 檢查真實的檔案類型 (Magic Bytes)
    actual_mime_type = magic.from_buffer(file_contents, mime=True)
    if actual_mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file content type detected: '{actual_mime_type}'. Upload rejected."
        )

    # 4. 如果所有檢查都通過，返回文件內容和安全檔名
    return file_contents, safe_filename