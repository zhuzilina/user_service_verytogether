"""
Django管理命令：创建测试用户用于RBAC权限测试
"""

from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from apps.users.models import User


class Command(BaseCommand):
    help = '创建具有不同角色的测试用户用于RBAC权限测试'

    def handle(self, *args, **options):
        test_users = [
            {
                'userid': 'super_admin01',
                'username': 'super_admin01',
                'email': 'super_admin01@test.com',
                'passwd': 'TestPass123!',
                'role': 'super_admin',
                'description': '超级管理员'
            },
            {
                'userid': 'competition_admin01',
                'username': 'competition_admin01',
                'email': 'competition_admin01@test.com',
                'passwd': 'TestPass123!',
                'role': 'competition_admin',
                'description': '学院学科竞赛管理员'
            },
            {
                'userid': 'teacher01',
                'username': 'teacher01',
                'email': 'teacher01@test.com',
                'passwd': 'TestPass123!',
                'role': 'teacher',
                'description': '学院教师'
            },
            {
                'userid': 'student01',
                'username': 'student01',
                'email': 'student01@test.com',
                'passwd': 'TestPass123!',
                'role': 'student',
                'description': '学院学生'
            },
            {
                'userid': 'student02',
                'username': 'student02',
                'email': 'student02@test.com',
                'passwd': 'TestPass123!',
                'role': 'student',
                'description': '学院学生'
            }
        ]

        self.stdout.write(self.style.SUCCESS('开始创建测试用户...'))

        for user_data in test_users:
            userid = user_data['userid']
            description = user_data.pop('description')

            try:
                # 检查用户是否已存在
                if User.objects.filter(userid=userid).exists():
                    user = User.objects.get(userid=userid)
                    self.stdout.write(
                        self.style.WARNING(f'用户 {userid} ({description}) 已存在')
                    )
                else:
                    # 创建新用户
                    user = User.objects.create(
                        userid=user_data['userid'],
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role']
                    )
                    user.set_password(user_data['passwd'])
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 创建用户: {userid} ({description})')
                    )

                # 创建或获取token
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  生成新Token: {token.key}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  已有Token: {token.key}')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'创建用户 {userid} 失败: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('\n测试用户创建完成!'))
        self.stdout.write(self.style.WARNING('\n用户权限级别说明:'))
        self.stdout.write('  超级管理员 (super_admin): 最高权限，可以管理所有功能')
        self.stdout.write('  竞赛管理员 (competition_admin): 可以管理竞赛、团队、成员')
        self.stdout.write('  教师 (teacher): 可以创建竞赛、管理团队、查看学生信息')
        self.stdout.write('  学生 (student): 基础权限，只能查看和参与')

        # 显示所有用户
        self.stdout.write(self.style.SUCCESS('\n当前系统用户:'))
        for user in User.objects.all():
            token = Token.objects.get_or_create(user=user)[0]
            self.stdout.write(
                f'  {user.userid} ({user.role}) - Token: {token.key}'
            )