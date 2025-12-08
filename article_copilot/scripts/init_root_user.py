"""初始化 Root 使用者腳本"""
import sys
from pathlib import Path

# 將專案根目錄加入 Python Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from article_copilot.models.domain.user import User
from article_copilot.daos.mongo_db.user_mongo_dao import get_user_dao
from article_copilot.security.login import get_password_hash
from article_copilot.enum.auth import Authorities
from article_copilot.util.function_utils import generate_id
from article_copilot.configs.logger_setting import log


def create_root_user(email: str = "admin@example.com", password: str = "Admin@123456"):
    """
    建立 Root 使用者
    
    Args:
        email: Root 使用者的 email (預設: admin@example.com)
        password: Root 使用者的密碼 (預設: Admin@123456)
    """
    user_dao = get_user_dao()
    
    # 檢查是否已存在
    existing_user = user_dao.find_by_email_address(email)
    if existing_user:
        print(f"⚠️  Root 使用者已存在: {email}")
        return False
    
    # 建立 Root 使用者
    root_user = User(
        id=str(generate_id()),
        email_address=email,
        hashed_password=get_password_hash(password),
        authority=Authorities.SYS_ADMIN,
        name="System Administrator"
    )
    
    # 儲存到資料庫
    success = user_dao.save(root_user)
    
    if success:
        print("=" * 60)
        print("✅ Root 使用者建立成功!")
        print("=" * 60)
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"👤 User ID: {root_user.id}")
        print(f"🛡️  Authority: {Authorities.SYS_ADMIN}")
        print("=" * 60)
        print("⚠️  請務必變更預設密碼!")
        print("=" * 60)
        log.info(f"Root user created: {root_user.id}")
        return True
    else:
        print("❌ Root 使用者建立失敗!")
        log.error("Failed to create root user")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化 Root 使用者")
    parser.add_argument(
        "--email",
        type=str,
        default="admin@example.com",
        help="Root 使用者的 email (預設: admin@example.com)"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="Admin@123456",
        help="Root 使用者的密碼 (預設: Admin@123456)"
    )
    
    args = parser.parse_args()
    
    print("🚀 開始建立 Root 使用者...")
    create_root_user(args.email, args.password)