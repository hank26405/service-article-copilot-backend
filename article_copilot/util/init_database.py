"""資料庫初始化工具"""
from article_copilot.models.domain.user import User
from article_copilot.daos.mongo_db.user_mongo_dao import get_user_dao
from article_copilot.security.login import get_password_hash
from article_copilot.enum.auth import Authorities
from article_copilot.util.function_utils import generate_id
from article_copilot.configs.logger_setting import log
from article_copilot.configs.project_setting import service_config


def ensure_root_user_exists():
    """
    確保 Root 使用者存在
    如果不存在則自動建立
    
    這個函數會在應用啟動時被呼叫
    """
    user_dao = get_user_dao()
    
    # 檢查是否有任何管理員使用者
    try:
        all_users = user_dao.find_all()
        if all_users:
            admins = [u for u in all_users if u.authority == Authorities.SYS_ADMIN]
            if admins:
                log.info(f"Found {len(admins)} admin user(s)")
                return True
    except Exception as e:
        log.error(f"Failed to check existing users: {e}")
    
    # 沒有管理員,建立預設 Root 使用者
    log.warning("No admin user found, creating default root user...")
    
    
    root_user = User(
        id=str(generate_id()),
        email_address=service_config.root_user_email,
        hashed_password=get_password_hash(service_config.root_user_password),
        authority=Authorities.SYS_ADMIN,
        name="System Administrator"
    )
    
    success = user_dao.save(root_user)
    
    if success:
        log.warning("=" * 60)
        log.warning("⚠️  DEFAULT ROOT USER CREATED ⚠️")
        log.warning("=" * 60)
        log.warning(f"Email: {service_config.root_user_email}")
        log.warning(f"Password: {service_config.root_user_password}")
        log.warning("=" * 60)
        log.warning("🔒 PLEASE CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")
        log.warning("=" * 60)
        return True
    else:
        log.error("Failed to create default root user!")
        return False


def initialize_database():
    """
    初始化資料庫
    - 建立必要的索引
    - 確保 Root 使用者存在
    """
    log.info("Initializing database...")
    
    # 確保 Root 使用者存在
    ensure_root_user_exists()
    
    log.info("Database initialization completed")