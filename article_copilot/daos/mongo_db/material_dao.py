import gridfs
from bson.objectid import ObjectId
from typing import Optional, List
from pymongo.errors import PyMongoError
from pymongo.database import Database

from article_copilot.models.domain.material import Material
from article_copilot.util.mongodb_client import get_mongodb_database

class MongoDBMaterialDAO:
    """
    MongoDB 素材資料存取層
    負責 Material Metadata CRUD 與 GridFS 檔案操作
    """
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_mongodb_database()
        self.collection = self.db["materials"]
        # 初始化 GridFS Bucket
        self.fs = gridfs.GridFS(self.db)
        self._create_indexes()
    
    def _create_indexes(self):
        """建立索引"""
        try:
            # 依 material_id 查詢 (唯一)
            self.collection.create_index("material_id", unique=True, background=True)
            # 依 user_id 查詢 (列出使用者的所有素材)
            self.collection.create_index("user_id", background=True)
            # 依 created_at 排序 (顯示最新素材)
            self.collection.create_index([("user_id", 1), ("created_at", -1)], background=True)
            # 依 shared_with_users 查詢 (列出被分享的素材)
            self.collection.create_index("shared_with_users", background=True)
            self.collection.create_index(
                [("user_id", 1), ("filename", 1)], 
                unique=True, 
                background=True,
                name="user_filename_unique"
            )
            print("✓ MongoDB Material indexes created successfully")
        except Exception as e:
            print(f"⚠ MongoDB Material index creation warning: {e}")

    # --- Metadata Operations ---

    def save_material(self, material: Material) -> bool:
        """儲存或更新素材 Metadata"""
        try:
            mat_dict = material.model_dump()
            self.collection.update_one(
                {"material_id": material.material_id},
                {"$set": mat_dict},
                upsert=True
            )
            return True
        except PyMongoError as e:
            if "user_filename_unique" in str(e) or "duplicate key" in str(e):
                print(f"✗ Duplicate filename for user {material.user_id}: {material.filename}")
                raise ValueError(f"檔名 '{material.filename}' 已存在，請使用不同的檔名")
            print(f"✗ Failed to save material metadata: {e}")
            return False

    def get_material(self, material_id: str) -> Optional[Material]:
        """讀取單一素材 Metadata"""
        try:
            data = self.collection.find_one({"material_id": material_id})
            if data:
                data.pop('_id', None)
                return Material.model_validate(data)
            return None
        except PyMongoError as e:
            print(f"✗ Failed to get material: {e}")
            return None

    def list_user_materials(self, user_id: str, limit: int = 50) -> List[Material]:
        """列出使用者擁有的所有素材 (依時間倒序)"""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            materials = []
            for doc in cursor:
                doc.pop('_id', None)
                materials.append(Material.model_validate(doc))
            return materials
        except PyMongoError as e:
            print(f"✗ Failed to list materials: {e}")
            return []

    def list_shared_materials(self, user_id: str, limit: int = 50) -> List[Material]:
        """列出分享給使用者的所有素材 (依時間倒序)"""
        try:
            cursor = self.collection.find(
                {"shared_with_users": user_id}
            ).sort("created_at", -1).limit(limit)
            materials = []
            for doc in cursor:
                doc.pop('_id', None)
                materials.append(Material.model_validate(doc))
            return materials
        except PyMongoError as e:
            print(f"✗ Failed to list shared materials: {e}")
            return []

    def list_all_accessible_materials(self, user_id: str, limit: int = 100) -> List[Material]:
        """列出使用者可存取的所有素材 (擁有 + 被分享)"""
        try:
            cursor = self.collection.find(
                {"$or": [
                    {"user_id": user_id},
                    {"shared_with_users": user_id}
                ]}
            ).sort("created_at", -1).limit(limit)
            materials = []
            for doc in cursor:
                doc.pop('_id', None)
                materials.append(Material.model_validate(doc))
            return materials
        except PyMongoError as e:
            print(f"✗ Failed to list accessible materials: {e}")
            return []

    def share_material_with_users(self, material_id: str, user_ids: List[str]) -> bool:
        """將素材分享給指定使用者 (新增到 shared_with_users)"""
        try:
            result = self.collection.update_one(
                {"material_id": material_id},
                {"$addToSet": {"shared_with_users": {"$each": user_ids}}}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except PyMongoError as e:
            print(f"✗ Failed to share material: {e}")
            return False

    def unshare_material_with_users(self, material_id: str, user_ids: List[str]) -> bool:
        """取消分享給指定使用者 (從 shared_with_users 移除)"""
        try:
            result = self.collection.update_one(
                {"material_id": material_id},
                {"$pullAll": {"shared_with_users": user_ids}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"✗ Failed to unshare material: {e}")
            return False

    def check_filename_exists(self, user_id: str, filename: str) -> bool:
        """檢查使用者是否已有相同檔名的素材"""
        try:
            count = self.collection.count_documents({
                "user_id": user_id,
                "filename": filename
            })
            return count > 0
        except PyMongoError as e:
            print(f"✗ Failed to check filename: {e}")
            return False

    # --- GridFS Operations ---

    def save_file_to_gridfs(self, file_content: bytes, filename: str, content_type: str) -> str:
        """
        將二進位檔案存入 GridFS
        :return: GridFS 的 file_id (字串格式)
        """
        file_id = self.fs.put(
            file_content, 
            filename=filename, 
            content_type=content_type
        )
        return str(file_id)

    def get_file_from_gridfs(self, gridfs_id: str) -> Optional[bytes]:
        """從 GridFS 讀取二進位檔案"""
        try:
            if not gridfs_id:
                return None
            return self.fs.get(ObjectId(gridfs_id)).read()
        except (gridfs.NoFile, Exception) as e:
            print(f"✗ Failed to read file from GridFS: {e}")
            return None

    def delete_material_completely(self, material_id: str) -> bool:
        """
        完整刪除素材 (同時刪除 Metadata 和 GridFS 中的檔案)
        """
        try:
            material = self.get_material(material_id)
            if not material:
                return False
            
            # 1. 刪除 GridFS 檔案
            if material.gridfs_id:
                try:
                    self.fs.delete(ObjectId(material.gridfs_id))
                except Exception as e:
                    print(f"⚠ Warning: Failed to delete GridFS file {material.gridfs_id}: {e}")

            # 2. 刪除 Metadata
            result = self.collection.delete_one({"material_id": material_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            print(f"✗ Failed to delete material: {e}")
            return False

# --- Factory ---
_material_dao_instance = None

def get_material_dao() -> MongoDBMaterialDAO:
    global _material_dao_instance
    if _material_dao_instance is None:
        _material_dao_instance = MongoDBMaterialDAO()
    return _material_dao_instance