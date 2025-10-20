"""
RBAC权限中间件
基于角色的访问控制中间件，用于API权限验证
"""

import logging
from typing import List, Optional, Set, Union

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from ..authentication import JWTAuthentication

from ..permissions.definitions import (
    has_permission,
    has_any_permission,
    has_all_permissions,
    Permission
)

logger = logging.getLogger(__name__)


class RBACMiddleware(MiddlewareMixin):
    """RBAC权限中间件"""

    # 不需要权限检查的路径
    PUBLIC_PATHS = {
        '/api/v1/auth/login/',
        '/api/v1/auth/logout/',
        '/api/v1/auth/refresh/',
        '/api/health/',
        '/api/status/',
        '/api/docs/',
        '/api/redoc/',
        '/admin/',
    }

    # 需要认证但不需要特殊权限的路径
    AUTH_ONLY_PATHS = {
        '/api/v1/auth/change-password/',
        '/api/v1/users/me/',
        '/api/v1/users/deactivate/',
    }

    # 以这些前缀开头的路径不需要权限检查
    PUBLIC_PATH_PREFIXES = {
        '/static/',
        '/media/',
        '/api/schema/',
    }

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.token_authenticator = TokenAuthentication()
        self.jwt_authenticator = JWTAuthentication()

    def is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        # 精确匹配公开路径
        if path in self.PUBLIC_PATHS:
            return True

        # 前缀匹配公开路径
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    def is_auth_only_path(self, path: str) -> bool:
        """检查是否为只需要认证的路径"""
        # 精确匹配认证路径
        if path in self.AUTH_ONLY_PATHS:
            return True

        # 检查用户ViewSet的自定义操作
        if path.startswith('/api/v1/users/') and path.endswith('/'):
            path_without_slash = path.rstrip('/')
            if path_without_slash.endswith('/me') or path_without_slash.endswith('/deactivate'):
                return True

        return False

    def get_required_permissions(self, path: str, method: str) -> Set[str]:
        """根据路径和方法获取所需权限"""
        # 标准化路径格式
        path = path.rstrip('/')
        method = method.upper()

        # 权限映射表 - 只包含实际存在的API端点
        permission_map = {
            # 用户管理 API (/api/v1/users/)
            ('/api/v1/users', 'GET'): {Permission.USER_LIST.value},
            ('/api/v1/users', 'POST'): {Permission.USER_CREATE.value},
            ('/api/v1/users/', 'GET'): {Permission.USER_LIST.value},
            ('/api/v1/users/', 'POST'): {Permission.USER_CREATE.value},

            # 用户详情 API (/api/v1/users/{id}/) - retrieve操作允许查看自己
            ('/api/v1/users/', 'GET'): {Permission.USER_READ.value},
            ('/api/v1/users/', 'PUT'): {Permission.USER_UPDATE.value},
            ('/api/v1/users/', 'PATCH'): {Permission.USER_UPDATE.value},
            ('/api/v1/users/', 'DELETE'): {Permission.USER_DELETE.value},

            # 用户活动 API (/api/v1/activities/)
            ('/api/v1/activities', 'GET'): {Permission.ACTIVITY_LIST.value},
            ('/api/v1/activities/', 'GET'): {Permission.ACTIVITY_LIST.value},
            ('/api/v1/activities/', 'GET'): {Permission.ACTIVITY_READ.value},

            # 用户自定义操作
            ('/api/v1/users/', 'POST'): set(),  # deactivate action
            ('/api/v1/users/', 'POST'): set(),  # activate action
            ('/api/v1/users/', 'PATCH'): set(),  # set_role action
        }

        # 特殊处理：用户详情查看允许查看自己的信息
        if path.startswith('/api/v1/users/') and method == 'GET':
            # 如果是查看用户详情，允许查看自己的信息
            if len(path.strip('/').split('/')) >= 4:  # /api/v1/users/{id}/ 格式
                return {Permission.USER_READ.value}

        # 尝试精确匹配
        if (path, method) in permission_map:
            return permission_map[(path, method)]

        # 尝试模式匹配
        for (pattern_path, pattern_method), permissions in permission_map.items():
            if method == pattern_method and self.path_matches(path, pattern_path):
                return permissions

        # 默认需要基础读权限
        if method == 'GET':
            return {Permission.USER_READ.value}

        # 默认需要基础写权限
        return {Permission.USER_UPDATE.value}

    def path_matches(self, path: str, pattern: str) -> bool:
        """检查路径是否匹配模式"""
        # 简单的路径匹配，可以扩展为更复杂的模式匹配
        if pattern.endswith('/'):
            return path.startswith(pattern)
        else:
            return path == pattern or path.startswith(pattern + '/')

    def extract_resource_id(self, path: str) -> Optional[str]:
        """从路径中提取资源ID"""
        parts = path.strip('/').split('/')
        if len(parts) >= 3 and parts[1].isdigit():
            return parts[1]
        return None

    def authenticate_user(self, request):
        """验证用户身份"""
        # Try JWT authentication first
        try:
            auth_result = self.jwt_authenticator.authenticate(request)
            if auth_result is not None:
                return auth_result[0]  # 返回用户对象
        except AuthenticationFailed:
            # JWT authentication failed, try token auth as fallback
            pass

        # Fallback to DRF Token authentication
        try:
            auth_result = self.token_authenticator.authenticate(request)
            if auth_result is not None:
                return auth_result[0]  # 返回用户对象

            # Try to get token from Authorization header directly
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
                try:
                    token = Token.objects.select_related('user').get(key=token_key)
                    return token.user
                except Token.DoesNotExist:
                    return None
            return None
        except AuthenticationFailed as e:
            logger.warning(f"认证失败: {e}")
            return None

    def check_user_permissions(self, user, required_permissions: Set[str]) -> bool:
        """检查用户权限"""
        if not user or not hasattr(user, 'role'):
            return False

        # 超级管理员跳过权限检查
        if hasattr(user, 'is_super_admin') and user.is_super_admin:
            return True

        # 检查是否具有所需权限
        return any(has_permission(user.role, perm) for perm in required_permissions)

    def check_resource_ownership(self, user, path: str, method: str) -> bool:
        """检查资源所有权（某些操作只能由资源所有者执行）"""
        if method in ['GET', 'HEAD', 'OPTIONS']:
            return True  # 读操作默认允许

        resource_id = self.extract_resource_id(path)
        if not resource_id:
            return True  # 无法提取资源ID时跳过检查

        # 检查是否为用户自己的资源
        if '/api/users/' in path:
            try:
                if hasattr(user, 'id') and str(user.id) == resource_id:
                    return True
                if hasattr(user, 'userid') and user.userid == resource_id:
                    return True
            except (ValueError, AttributeError):
                pass

        return False

    def process_request(self, request):
        """处理请求"""
        path = request.path
        method = request.method

        # 检查是否为公开路径
        if self.is_public_path(path):
            return None

        # 验证用户身份
        user = self.authenticate_user(request)
        if not user:
            return JsonResponse({
                'error': '身份验证失败',
                'message': '请提供有效的认证令牌',
                'code': 'AUTHENTICATION_REQUIRED'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 将用户添加到请求对象
        request.user = user

        # 检查是否为只需要认证的路径（不需要特殊权限）
        if self.is_auth_only_path(path):
            # 对于只需要认证的路径，跳过权限检查但仍检查资源所有权
            if not self.check_resource_ownership(user, path, method):
                logger.warning(
                    f"资源所有权检查失败 - 用户: {getattr(user, 'userid', 'unknown')}, "
                    f"路径: {path}, 方法: {method}"
                )
                return JsonResponse({
                    'error': '资源所有权错误',
                    'message': '您只能操作自己的资源',
                    'code': 'RESOURCE_OWNERSHIP_REQUIRED'
                }, status=status.HTTP_403_FORBIDDEN)
            return None

        # 获取所需权限
        required_permissions = self.get_required_permissions(path, method)

        # 检查权限
        if not self.check_user_permissions(user, required_permissions):
            logger.warning(
                f"权限不足 - 用户: {getattr(user, 'userid', 'unknown')}, "
                f"角色: {getattr(user, 'role', 'unknown')}, "
                f"路径: {path}, 方法: {method}, "
                f"所需权限: {required_permissions}"
            )
            return JsonResponse({
                'error': '权限不足',
                'message': '您没有执行此操作的权限',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'required_permissions': list(required_permissions),
                'user_role': getattr(user, 'role', None)
            }, status=status.HTTP_403_FORBIDDEN)

        # 检查资源所有权
        if not self.check_resource_ownership(user, path, method):
            logger.warning(
                f"资源所有权检查失败 - 用户: {getattr(user, 'userid', 'unknown')}, "
                f"路径: {path}, 方法: {method}"
            )
            return JsonResponse({
                'error': '资源所有权错误',
                'message': '您只能操作自己的资源',
                'code': 'RESOURCE_OWNERSHIP_REQUIRED'
            }, status=status.HTTP_403_FORBIDDEN)

        return None

    def process_response(self, request, response):
        """处理响应"""
        # 添加权限相关的响应头
        if hasattr(request, 'user') and request.user:
            response['X-User-Role'] = getattr(request.user, 'role', '')
            response['X-User-ID'] = str(getattr(request.user, 'userid', ''))

        return response