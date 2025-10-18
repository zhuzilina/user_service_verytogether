"""
System configuration management
"""

import os
from django.conf import settings


class SystemConfig:
    """system configuration management class"""

    @staticmethod
    def get_admin_password():
        """Get system admin password"""
        # Get from environment variables first
        password = os.environ.get('ADMIN_PASSWORD')
        if password:
            return password

        # 从Django settings获取
        password = getattr(settings, 'ADMIN_PASSWORD', None)
        if password:
            return password

        # Default password
        return 'admin123'

    @staticmethod
    def update_admin_password(new_password):
        """Update system admin password"""
        env_file = os.path.join(settings.BASE_DIR, '.env')

        try:
            # Read existing configuration
            lines = []
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()

            # Update or add ADMIN_PASSWORD
            found = False
            for i, line in enumerate(lines):
                if line.startswith('ADMIN_PASSWORD='):
                    lines[i] = f'ADMIN_PASSWORD={new_password}\n'
                    found = True
                    break

            if not found:
                lines.append(f'ADMIN_PASSWORD={new_password}\n')

            # Write file
            with open(env_file, 'w') as f:
                f.writelines(lines)

            return True
        except Exception as e:
            print(f"Failed to update configuration: {e}")
            return False

    @staticmethod
    def reload_admin_password():
        """Reload system admin password"""
        password = SystemConfig.get_admin_password()

        # Update system admin password
        from apps.users.models import User
        try:
            admin = User.objects.get(id=1, userid='admin', is_system_admin=True)
            admin.set_password(password)
            return True
        except User.DoesNotExist:
            return False