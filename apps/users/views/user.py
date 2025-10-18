"""
Views for simplified user management API endpoints with RBAC permissions.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema

from ..models import User, UserActivity
from ..serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserLoginSerializer, UserActivitySerializer, ChangePasswordSerializer,
    UserRoleUpdateSerializer, UserStatusUpdateSerializer
)
from ..decorators import (
    require_permissions, require_role, require_super_admin,
    require_competition_admin_or_above, require_teacher_or_above,
    require_minimum_role, resource_owner_or_admin
)
from ..permissions.definitions import Permission
from ..exceptions import handle_system_admin_protection


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user accounts with RBAC permissions.
    Provides CRUD operations for user management with simplified structure.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        # 超级管理员和竞赛管理员可以看到所有用户
        if hasattr(user, 'is_admin') and user.is_admin:
            return User.objects.all()
        # 教师可以看到学生和教师角色用户
        elif hasattr(user, 'is_teacher') and user.is_teacher:
            return User.objects.filter(role__in=['student', 'teacher'])
        # 学生只能看到自己
        else:
            return User.objects.filter(id=user.id)

    @require_super_admin
    def create(self, request, *args, **kwargs):
        """创建新用户 - 仅超级管理员"""
        return super().create(request, *args, **kwargs)

    @require_permissions(Permission.USER_READ.value)
    def retrieve(self, request, *args, **kwargs):
        """获取用户详情 - 需要用户读取权限"""
        return super().retrieve(request, *args, **kwargs)

    @require_super_admin
    def list(self, request, *args, **kwargs):
        """获取用户列表 - 仅超级管理员"""
        return super().list(request, *args, **kwargs)

    @require_super_admin
    def update(self, request, *args, **kwargs):
        """更新用户信息 - 仅超级管理员"""
        return super().update(request, *args, **kwargs)

    @require_super_admin
    def partial_update(self, request, *args, **kwargs):
        """部分更新用户信息 - 仅超级管理员"""
        return super().partial_update(request, *args, **kwargs)

    @require_super_admin
    def destroy(self, request, *args, **kwargs):
        """删除用户 - 仅超级管理员"""
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Create user and log activity."""
        with transaction.atomic():
            user = serializer.save()
            # Log user creation activity
            UserActivity.objects.create(
                user=user,
                action='register',
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            )

    def perform_update(self, serializer):
        """Update user and log activity."""
        with transaction.atomic():
            serializer.save()
            UserActivity.objects.create(
                user=self.get_object(),
                action='update_profile',
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            )

    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @extend_schema(
        summary="获取当前用户信息",
        description="获取已认证用户的详细信息",
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="停用用户账户",
        description="停用当前用户的账户",
        responses={204: "No Content"}
    )
    @action(detail=False, methods=['delete'])
    def deactivate(self, request):
        """Deactivate current user account."""
        user = request.user
        user.deactivate()

        UserActivity.objects.create(
            user=user,
            action='deactivate',
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="激活用户账户",
        description="激活用户账户（需要管理员权限）",
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['post'])
    @require_competition_admin_or_above
    def activate(self, request, pk=None):
        """Activate user account (admin only)."""
        user = self.get_object()
        user.activate()

        UserActivity.objects.create(
            user=user,
            action='activate',
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="更新用户角色",
        description="更新用户角色（仅超级管理员）",
        request=UserRoleUpdateSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'])
    @require_super_admin
    def set_role(self, request, pk=None):
        """Update user role (super admin only)."""
        user = self.get_object()
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        UserActivity.objects.create(
            user=user,
            action='update_profile',  # Use existing action type
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return Response(serializer.data)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user activities with RBAC permissions.
    """
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter activities based on user permissions."""
        user = self.request.user
        # 超级管理员和竞赛管理员可以看到所有活动
        if hasattr(user, 'is_admin') and user.is_admin:
            return UserActivity.objects.all().order_by('-created_at')
        # 教师可以看到学生和教师的活动
        elif hasattr(user, 'is_teacher') and user.is_teacher:
            teacher_and_student_ids = User.objects.filter(
                role__in=['student', 'teacher']
            ).values_list('id', flat=True)
            return UserActivity.objects.filter(
                user_id__in=teacher_and_student_ids
            ).order_by('-created_at')
        # 学生只能看到自己的活动
        else:
            return UserActivity.objects.filter(user=user).order_by('-created_at')

    @require_permissions(Permission.ACTIVITY_LIST.value)
    def list(self, request, *args, **kwargs):
        """获取活动列表 - 需要活动列表权限"""
        return super().list(request, *args, **kwargs)

    @require_permissions(Permission.ACTIVITY_READ.value)
    def retrieve(self, request, *args, **kwargs):
        """获取活动详情 - 需要活动读取权限"""
        return super().retrieve(request, *args, **kwargs)


class LoginView(APIView):
    """
    Custom login view that returns user data along with token.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="用户登录",
        description="用户认证并返回访问令牌",
        request=UserLoginSerializer,
        responses={200: {"type": "object", "properties": {
            "token": {"type": "string"},
            "user": UserSerializer
        }}}
    )
    def post(self, request, *args, **kwargs):
        """Handle user login."""
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Create or get token
        token, created = Token.objects.get_or_create(user=user)

        # Update last login time
        user.update_last_login_time()

        # Log activity
        UserActivity.objects.create(
            user=user,
            action='login',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    View for user logout.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="用户登出",
        description="用户登出并使访问令牌失效",
        responses={204: "No Content"}
    )
    def post(self, request):
        """Handle user logout."""
        try:
            # Delete user's token
            request.user.auth_token.delete()
        except Token.DoesNotExist:
            pass

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='logout',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(APIView):
    """
    View for user registration - Super Admin only.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserCreateSerializer

    @extend_schema(
        summary="用户注册",
        description="注册新的用户账户（仅超级管理员）",
        request=UserCreateSerializer,
        responses={201: UserSerializer}
    )
    @require_super_admin
    def post(self, request):
        """Handle user registration."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

            # Create auth token
            token, created = Token.objects.get_or_create(user=user)

            # Log activity
            UserActivity.objects.create(
                user=user,
                action='register',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )

            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ChangePasswordView(APIView):
    """
    View for changing user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        summary="修改密码",
        description="修改已认证用户的密码（系统根管理员不允许）",
        request=ChangePasswordSerializer,
        responses={204: "No Content"}
    )
    @handle_system_admin_protection
    def post(self, request):
        """Handle password change."""
        # 检查是否为系统根管理员
        if hasattr(request.user, 'is_system_root_admin') and request.user.is_system_root_admin:
            from ..exceptions import SystemAdminProtectionError
            raise SystemAdminProtectionError("系统根管理员密码只能通过配置文件修改")

        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Log activity
        UserActivity.objects.create(
            user=user,
            action='change_password',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip