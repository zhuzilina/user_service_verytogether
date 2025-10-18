"""
User model for UserService microservice.
Simplified structure with basic authentication fields only.
"""
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    Simplified User model for microservice architecture.
    Contains only essential fields: id, userid, passwd, role.
    """
    # Required by Django's authentication system
    username = models.CharField(max_length=50, unique=True, db_index=True, help_text="用户名")
    email = models.EmailField(unique=True, db_index=True, help_text="邮箱")

    # Core fields
    userid = models.CharField(max_length=50, unique=True, db_index=True, help_text="用户ID")
    passwd = models.CharField(max_length=128, help_text="加密后的密码")
    role = models.CharField(
        max_length=30,
        choices=[
            ('super_admin', '超级管理员'),
            ('competition_admin', '学院学科竞赛管理员'),
            ('teacher', '学院教师'),
            ('student', '学院学生'),
        ],
        default='student',
        db_index=True,
        help_text="用户角色"
    )

    # 系统管理员标识（用于唯一超级管理员）
    is_system_admin = models.BooleanField(
        default=False,
        db_index=True,
        help_text="是否为系统根管理员"
    )

    # Status fields
    is_active = models.BooleanField(default=True, db_index=True, help_text="用户是否激活")
    is_staff = models.BooleanField(default=False, help_text="是否为员工")
    is_superuser = models.BooleanField(default=False, help_text="是否为超级用户")
    last_login = models.DateTimeField(null=True, blank=True, help_text="最后登录时间")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="创建时间")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新时间")

    # Required by Django's authentication system
    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['email']

    # Role choices as class attribute for easier access
    ROLE_CHOICES = [
        ('super_admin', '超级管理员'),
        ('competition_admin', '学院学科竞赛管理员'),
        ('teacher', '学院教师'),
        ('student', '学院学生'),
    ]

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        indexes = [
            models.Index(fields=['userid']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['userid', 'role']),  # 复合索引
        ]

    def __str__(self):
        return f"User({self.userid}, {self.role})"

    def get_full_name(self):
        """Django认证系统要求的方法"""
        return self.userid

    def get_short_name(self):
        """Django认证系统要求的方法"""
        return self.userid

    def set_password(self, raw_password):
        """设置加密密码"""
        self.passwd = make_password(raw_password)

        # 系统根管理员只更新密码字段，不触发其他检查
        if self.is_system_root_admin:
            self.save(update_fields=['passwd'])
        else:
            self.save(update_fields=['passwd', 'updated_at'])

    def check_password(self, raw_password):
        """验证密码"""
        return check_password(raw_password, self.passwd)

    def has_perm(self, perm, obj=None):
        """检查权限"""
        return self.is_superuser or self.is_staff

    def has_perms(self, perm_list, obj=None):
        """检查多个权限"""
        return self.has_perm(None)

    def has_module_perms(self, app_label):
        """检查模块权限"""
        return self.is_superuser or self.is_staff

    @property
    def is_super_admin(self):
        """检查是否为超级管理员"""
        return self.role == 'super_admin' or self.is_superuser

    @property
    def is_competition_admin(self):
        """检查是否为竞赛管理员"""
        return self.role == 'competition_admin'

    @property
    def is_teacher(self):
        """检查是否为教师"""
        return self.role == 'teacher'

    @property
    def is_student(self):
        """检查是否为学生"""
        return self.role == 'student'

    @property
    def is_admin(self):
        """检查是否为管理员（包含超级管理员和竞赛管理员）"""
        return self.role in ['super_admin', 'competition_admin'] or self.is_superuser

    @property
    def is_system_root_admin(self):
        """检查是否为系统根管理员（唯一的超级管理员）"""
        return self.is_system_admin and self.id == 1 and self.userid == 'admin'

    def update_last_login_time(self):
        """更新最后登录时间"""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])

    def deactivate(self):
        """停用用户"""
        # 系统根管理员不能被停用
        if self.is_system_root_admin:
            raise ValueError("系统根管理员不能被停用")

        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def activate(self):
        """激活用户"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    @property
    def groups(self):
        """Django认证系统要求的属性"""
        return []

    @property
    def user_permissions(self):
        """Django认证系统要求的属性"""
        return []

    @property
    def is_anonymous(self):
        """Django认证系统要求的属性"""
        return False

    @property
    def is_authenticated(self):
        """Django认证系统要求的属性"""
        return True

    def save(self, *args, **kwargs):
        """重写保存方法，保护系统根管理员"""
        # 如果是系统根管理员，检查不允许修改的字段
        if self.pk and self.is_system_root_admin:
            # 获取数据库中的原始对象
            try:
                old_user = User.objects.get(pk=self.pk)
                # 检查关键字段是否被修改
                if old_user.userid != self.userid:
                    raise ValueError("系统根管理员的userid不能修改")
                if old_user.role != self.role:
                    raise ValueError("系统根管理员的角色不能修改")
                if self.id != 1:
                    raise ValueError("系统根管理员的ID必须为1")
            except User.DoesNotExist:
                if self.id != 1:
                    raise ValueError("系统根管理员的ID必须为1")
                if self.userid != 'admin':
                    raise ValueError("系统根管理器的userid必须为admin")
                if self.role != 'super_admin':
                    raise ValueError("系统根管理器的角色必须为super_admin")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """重写删除方法，保护系统根管理员"""
        if self.is_system_root_admin:
            raise ValueError("系统根管理员不能被删除")
        super().delete(*args, **kwargs)


class UserActivity(models.Model):
    """
    用户活动记录，用于审计和分析
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')

    # 活动详情
    action = models.CharField(
        max_length=50,
        choices=[
            ('login', '登录'),
            ('logout', '登出'),
            ('register', '注册'),
            ('update_profile', '更新资料'),
            ('change_password', '修改密码'),
            ('deactivate', '停用账户'),
            ('activate', '激活账户'),
        ],
        db_index=True,
        help_text="操作类型"
    )

    # 请求信息
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP地址")
    user_agent = models.TextField(blank=True, help_text="用户代理")

    # 状态信息
    success = models.BooleanField(default=True, help_text="操作是否成功")
    error_message = models.TextField(blank=True, help_text="错误信息")

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="创建时间")

    class Meta:
        db_table = 'user_activities'
        verbose_name = '用户活动'
        verbose_name_plural = '用户活动'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'action']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.userid} - {self.action} at {self.created_at}"