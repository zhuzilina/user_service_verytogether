"""
Django管理命令：更新系统管理员密码
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.users.models import User
from apps.users.config import SystemConfig


class Command(BaseCommand):
    help = '更新系统管理员密码'

    def add_arguments(self, parser):
        parser.add_argument(
            'password',
            type=str,
            help='新的管理员密码',
        )
        parser.add_argument(
            '--save-config',
            action='store_true',
            help='同时更新配置文件',
        )

    def handle(self, *args, **options):
        new_password = options['password']
        save_config = options.get('save_config', False)

        if len(new_password) < 6:
            self.stdout.write(
                self.style.ERROR('密码长度不能少于6个字符')
            )
            return

        try:
            # 获取系统管理员
            admin_user = User.objects.get(id=1, userid='admin', is_system_admin=True)

            # 更新密码
            admin_user.set_password(new_password)
            self.stdout.write(
                self.style.SUCCESS(f'✓ 系统管理员密码已更新')
            )

            # 如果需要，更新配置文件
            if save_config:
                if SystemConfig.update_admin_password(new_password):
                    self.stdout.write(
                        self.style.SUCCESS('✓ 配置文件已更新')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠ 配置文件更新失败')
                    )

            self.stdout.write(
                self.style.WARNING('\n注意：')
            )
            self.stdout.write('- 系统根管理员密码已更新')
            if save_config:
                self.stdout.write('- 配置文件已更新，重启服务后生效')
            else:
                self.stdout.write('- 配置文件未更新，仅本次会话生效')

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('系统管理员不存在，请先运行 init_superuser')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'更新密码失败: {str(e)}')
            )