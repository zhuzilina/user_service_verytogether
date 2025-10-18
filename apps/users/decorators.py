"""
RBAC Permission Decorator
Permission control for the view level
"""

import functools
import logging
from typing import List, Set, Union

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions.definitions import (
    has_permission,
    has_any_permission,
    has_all_permissions,
    Permission,
    get_user_accessible_permissions
)

logger = logging.getLogger(__name__)


def require_permissions(permissions: Union[str, List[str]], require_all: bool = False):
    """
    权限检查装饰器

    Args:
        permissions: 所需权限，可以是单个权限字符串或权限列表
        require_all: 是否需要拥有所有权限，False表示只需要其中任一权限
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # 检查用户是否已认证
            if not hasattr(request, 'user') or not request.user:
                return Response({
                    'error': '身份验证失败',
                    'message': '请先登录',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)

            user = request.user

            # 超级管理员跳过权限检查
            if hasattr(user, 'is_super_admin') and user.is_super_admin:
                return view_func(view_instance, request, *args, **kwargs)

            # 标准化权限列表
            if isinstance(permissions, str):
                required_permissions = [permissions]
            else:
                required_permissions = permissions

            # 检查权限
            if require_all:
                has_perms = has_all_permissions(user.role, required_permissions)
                error_message = '您需要拥有所有权限才能执行此操作'
            else:
                has_perms = has_any_permission(user.role, required_permissions)
                error_message = '您需要拥有其中任一权限才能执行此操作'

            if not has_perms:
                logger.warning(
                    f"权限不足 - 用户: {getattr(user, 'userid', 'unknown')}, "
                    f"角色: {getattr(user, 'role', 'unknown')}, "
                    f"视图: {view_instance.__class__.__name__}, "
                    f"所需权限: {required_permissions}"
                )
                return Response({
                    'error': '权限不足',
                    'message': error_message,
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_permissions': required_permissions,
                    'user_role': getattr(user, 'role', None)
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(view_instance, request, *args, **kwargs)

        return wrapper
    return decorator


def require_role(*allowed_roles: str):
    """
    角色检查装饰器

    Args:
        allowed_roles: 允许的角色列表
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # 检查用户是否已认证
            if not hasattr(request, 'user') or not request.user:
                return Response({
                    'error': '身份验证失败',
                    'message': '请先登录',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)

            user = request.user

            # 超级管理员跳过角色检查
            if hasattr(user, 'is_super_admin') and user.is_super_admin:
                return view_func(view_instance, request, *args, **kwargs)

            # 检查角色
            if getattr(user, 'role', None) not in allowed_roles:
                logger.warning(
                    f"角色权限不足 - 用户: {getattr(user, 'userid', 'unknown')}, "
                    f"当前角色: {getattr(user, 'role', 'unknown')}, "
                    f"允许角色: {allowed_roles}, "
                    f"视图: {view_instance.__class__.__name__}"
                )
                return Response({
                    'error': '角色权限不足',
                    'message': f'此操作仅允许以下角色执行: {", ".join(allowed_roles)}',
                    'code': 'ROLE_NOT_ALLOWED',
                    'allowed_roles': list(allowed_roles),
                    'user_role': getattr(user, 'role', None)
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(view_instance, request, *args, **kwargs)

        return wrapper
    return decorator


def require_super_admin(view_func):
    """超级管理员权限装饰器"""
    @functools.wraps(view_func)
    def wrapper(view_instance, request, *args, **kwargs):
        # 检查用户是否已认证
        if not hasattr(request, 'user') or not request.user:
            return Response({
                'error': '身份验证失败',
                'message': '请先登录',
                'code': 'AUTHENTICATION_REQUIRED'
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user

        # 系统根管理员跳过角色检查
        if hasattr(user, 'is_system_root_admin') and user.is_system_root_admin:
            return view_func(view_instance, request, *args, **kwargs)

        # 检查角色
        if getattr(user, 'role', None) != 'super_admin':
            logger.warning(
                f"角色权限不足 - 用户: {getattr(user, 'userid', 'unknown')}, "
                f"当前角色: {getattr(user, 'role', 'unknown')}, "
                f"视图: {view_instance.__class__.__name__}"
            )
            return Response({
                'error': '角色权限不足',
                'message': f'此操作仅允许超级管理员执行',
                'code': 'ROLE_NOT_ALLOWED',
                'allowed_roles': ['super_admin'],
                'user_role': getattr(user, 'role', None)
            }, status=status.HTTP_403_FORBIDDEN)

        return view_func(view_instance, request, *args, **kwargs)

    return wrapper


def require_competition_admin_or_above(view_func):
    """竞赛管理员及以上权限装饰器"""
    return require_role('super_admin', 'competition_admin')(view_func)


def require_teacher_or_above(view_func):
    """教师及以上权限装饰器"""
    return require_role('super_admin', 'competition_admin', 'teacher')(view_func)


def require_minimum_role(min_role: str):
    """
    最低角色权限装饰器

    Args:
        min_role: 最低要求的角色
    """
    role_hierarchy = {
        'student': 0,
        'teacher': 1,
        'competition_admin': 2,
        'super_admin': 3,
    }

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # 检查用户是否已认证
            if not hasattr(request, 'user') or not request.user:
                return Response({
                    'error': '身份验证失败',
                    'message': '请先登录',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)

            user = request.user
            user_role = getattr(user, 'role', None)

            # 超级管理员跳过检查
            if hasattr(user, 'is_super_admin') and user.is_super_admin:
                return view_func(view_instance, request, *args, **kwargs)

            # 检查角色等级
            if user_role not in role_hierarchy:
                return Response({
                    'error': '角色无效',
                    'message': f'用户角色 {user_role} 无效',
                    'code': 'INVALID_ROLE'
                }, status=status.HTTP_403_FORBIDDEN)

            user_level = role_hierarchy[user_role]
            required_level = role_hierarchy.get(min_role, 0)

            if user_level < required_level:
                logger.warning(
                    f"角色等级不足 - 用户: {getattr(user, 'userid', 'unknown')}, "
                    f"当前角色: {user_role} (等级: {user_level}), "
                    f"最低要求: {min_role} (等级: {required_level}), "
                    f"视图: {view_instance.__class__.__name__}"
                )
                return Response({
                    'error': '角色等级不足',
                    'message': f'此操作需要 {min_role} 角色或更高',
                    'code': 'ROLE_LEVEL_INSUFFICIENT',
                    'user_role': user_role,
                    'user_level': user_level,
                    'required_role': min_role,
                    'required_level': required_level
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(view_instance, request, *args, **kwargs)

        return wrapper
    return decorator


def resource_owner_or_admin(resource_id_param: str = 'pk'):
    """
    资源所有者或管理员权限装饰器

    Args:
        resource_id_param: 资源ID参数名
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # 检查用户是否已认证
            if not hasattr(request, 'user') or not request.user:
                return Response({
                    'error': '身份验证失败',
                    'message': '请先登录',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=status.HTTP_401_UNAUTHORIZED)

            user = request.user

            # 管理员跳过所有权检查
            if hasattr(user, 'is_admin') and user.is_admin:
                return view_func(view_instance, request, *args, **kwargs)

            # 获取资源ID
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                return view_func(view_instance, request, *args, **kwargs)  # 无资源ID时跳过检查

            # 检查是否为资源所有者
            is_owner = False
            if hasattr(user, 'id') and str(user.id) == str(resource_id):
                is_owner = True
            elif hasattr(user, 'userid') and user.userid == str(resource_id):
                is_owner = True

            if not is_owner:
                logger.warning(
                    f"资源所有权检查失败 - 用户: {getattr(user, 'userid', 'unknown')}, "
                    f"资源ID: {resource_id}, "
                    f"视图: {view_instance.__class__.__name__}"
                )
                return Response({
                    'error': '资源所有权错误',
                    'message': '您只能操作自己的资源',
                    'code': 'RESOURCE_OWNERSHIP_REQUIRED'
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(view_instance, request, *args, **kwargs)

        return wrapper
    return decorator


class PermissionMixin:
    """权限混入类，用于DRF视图"""

    required_permissions: Union[str, List[str]] = []
    require_all_permissions: bool = False

    def get_required_permissions(self):
        """获取所需权限"""
        return self.required_permissions

    def check_permissions(self, request):
        """检查权限"""
        super().check_permissions(request)

        if not request.user:
            return

        # 超级管理员跳过权限检查
        if hasattr(request.user, 'is_super_admin') and request.user.is_super_admin:
            return

        permissions = self.get_required_permissions()
        if not permissions:
            return

        # 标准化权限列表
        if isinstance(permissions, str):
            required_permissions = [permissions]
        else:
            required_permissions = permissions

        # 检查权限
        if self.require_all_permissions:
            has_perms = has_all_permissions(request.user.role, required_permissions)
        else:
            has_perms = has_any_permission(request.user.role, required_permissions)

        if not has_perms:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied({
                'error': '权限不足',
                'message': '您没有执行此操作的权限',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'required_permissions': required_permissions,
                'user_role': getattr(request.user, 'role', None)
            })


def auto_register_permissions(view_class):
    """
    自动注册权限装饰器 - 用于自动将视图权限注册到权限系统
    """
    # 这里可以实现自动权限注册逻辑
    # 例如将视图权限信息注册到数据库或配置文件中
    return view_class