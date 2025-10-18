"""
Django管理命令：系统初始化 - 创建唯一的超级管理员
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from rest_framework.authtoken.models import Token
from apps.users.models import User


class Command(BaseCommand):
    help = '初始化系统，创建唯一的超级管理员账户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建超级管理员账户',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('开始系统初始化...'))

        # 检查是否已存在超级管理员
        admin_user = None
        try:
            admin_user = User.objects.get(id=1)
            if not force and admin_user.userid == 'admin' and admin_user.role == 'super_admin':
                self.stdout.write(
                    self.style.WARNING('超级管理员已存在 (ID=1, userid=admin)')
                )
                token, created = Token.objects.get_or_create(user=admin_user)
                self.stdout.write(
                    self.style.SUCCESS(f'超级管理员Token: {token.key}')
                )
                return
        except User.DoesNotExist:
            pass

        # 如果存在且强制重新创建，先删除
        if admin_user and force:
            self.stdout.write(self.style.WARNING('删除现有超级管理员...'))
            Token.objects.filter(user=admin_user).delete()
            admin_user.delete()

        # 从环境变量或配置文件获取密码
        admin_password = self.get_admin_password()

        # 创建超级管理员
        try:
            admin_user = User.objects.create(
                id=1,  # 固定ID
                userid='admin',  # 固定用户名
                username='admin',
                email='admin@system.local',
                role='super_admin',
                is_system_admin=True,  # 系统根管理员标识
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )

            # 设置密码
            admin_user.set_password(admin_password)
            admin_user.save()

            # 创建Token
            token = Token.objects.create(user=admin_user)

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ 超级管理员创建成功:\n'
                    f'  ID: {admin_user.id}\n'
                    f'  用户名: {admin_user.userid}\n'
                    f'  角色: {admin_user.role}\n'
                    f'  Token: {token.key}\n'
                    f'  创建时间: {admin_user.created_at}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建超级管理员失败: {str(e)}')
            )
            return

        self.stdout.write(self.style.SUCCESS('系统初始化完成!'))

        self.stdout.write(self.style.WARNING('\n重要提示:'))
        self.stdout.write('1. 超级管理员账户是系统唯一的根管理员')
        self.stdout.write('2. 该账户ID恒为1，用户名恒为admin，不可修改')
        self.stdout.write('3. 只能通过配置文件修改密码，API无法修改')
        self.stdout.write('4. 该账户不能被删除或禁用')
        self.stdout.write('5. 请妥善保管Token和密码')

    def get_admin_password(self):
        """从环境变量或配置文件获取管理员密码"""
        # 优先从环境变量获取
        password = os.environ.get('ADMIN_PASSWORD')

        if not password:
            # 从Django settings获取
            password = getattr(settings, 'ADMIN_PASSWORD', None)

        if not password:
            # 默认密码（生产环境必须修改）
            password = 'Admin123!ChangeMe'
            self.stdout.write(
                self.style.WARNING(
                    '使用默认密码: Admin123!ChangeMe\n'
                    '生产环境请设置ADMIN_PASSWORD环境变量!'
                )
            )

        return password