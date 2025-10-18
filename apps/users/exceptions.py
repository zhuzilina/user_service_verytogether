"""
用户服务自定义异常
"""

from rest_framework import status
from rest_framework.response import Response


class SystemAdminProtectionError(Exception):
    """系统管理员保护异常"""
    pass


def handle_system_admin_protection(func):
    """系统管理员保护装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SystemAdminProtectionError as e:
            return Response({
                'error': '系统管理员保护',
                'message': str(e),
                'code': 'SYSTEM_ADMIN_PROTECTION'
            }, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            error_msg = str(e)
            if '系统根管理员' in error_msg:
                return Response({
                    'error': '系统管理员保护',
                    'message': error_msg,
                    'code': 'SYSTEM_ADMIN_PROTECTION'
                }, status=status.HTTP_403_FORBIDDEN)
            raise
    return wrapper