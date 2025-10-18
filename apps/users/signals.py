"""
Django信号处理模块
用于在系统启动时自动初始化系统根管理员用户
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_migrate)
def init_system_superuser(sender, **kwargs):
    """
    在数据库迁移完成后自动检查并初始化系统根管理员

    这个信号会在每次执行migrate命令后触发，确保系统根管理员存在
    """
    # 只在users应用的迁移完成后执行
    if sender.name == 'apps.users':
        try:
            _ensure_system_admin_exists()
        except Exception as e:
            logger.error(f"自动初始化系统根管理员失败: {e}")


def _ensure_system_admin_exists():
    """确保系统根管理员存在"""
    from .config import SystemConfig

    # 检查系统根管理员是否存在
    try:
        admin_user = User.objects.get(id=1, userid='admin', is_system_admin=True)
        logger.info("系统根管理员已存在")

        # 检查密码是否需要更新（从配置文件同步）
        config_password = SystemConfig.get_admin_password()
        if not admin_user.check_password(config_password):
            logger.info("检测到配置文件密码变更，更新系统根管理员密码")
            admin_user.set_password(config_password)
            admin_user.save()
            logger.info("系统根管理员密码已更新")

        return admin_user

    except User.DoesNotExist:
        # 系统根管理员不存在，需要创建
        logger.info("正在创建系统根管理员...")
        return _create_system_admin()


def _create_system_admin():
    """创建系统根管理员"""
    from .config import SystemConfig

    try:
        # 获取配置的密码
        password = SystemConfig.get_admin_password()

        # 创建系统根管理员
        admin_user = User.objects.create(
            id=1,  # 强制设置ID为1
            userid='admin',
            username='admin',
            email='admin@localhost',
            role='super_admin',
            is_system_admin=True,
            is_active=True,
            is_staff=True,
            is_superuser=True
        )

        # 设置密码
        admin_user.set_password(password)
        admin_user.save(update_fields=['passwd'])

        logger.info(f"✓ 系统根管理员创建成功")
        logger.info(f"  - 用户ID: admin")
        logger.info(f"  - 角色: 超级管理员")
        logger.info(f"  - 密码来源: {password if password != 'admin123' else '默认密码'}")

        return admin_user

    except Exception as e:
        logger.error(f"创建系统根管理员失败: {e}")
        raise


def ensure_system_admin_on_startup():
    """
    在应用启动时确保系统根管理员存在
    这个函数可以在中间件或视图中调用
    """
    try:
        _ensure_system_admin_exists()
    except Exception as e:
        logger.error(f"启动时检查系统根管理员失败: {e}")