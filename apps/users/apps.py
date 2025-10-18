from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'User Service'

    def ready(self):
        # Import signals when app is ready
        try:
            import apps.users.signals

            # 在应用启动时确保系统根管理员存在
            from .signals import ensure_system_admin_on_startup
            ensure_system_admin_on_startup()

        except ImportError:
            pass