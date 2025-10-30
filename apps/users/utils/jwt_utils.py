"""
JWT工具类
提供JWT令牌的生成、验证等功能
"""

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Any, Optional


class JWTUtils:
    """JWT工具类"""

    @staticmethod
    def generate_tokens(user) -> Dict[str, Any]:
        """为用户生成访问令牌和刷新令牌"""
        now = datetime.now()

        # 访问令牌载荷
        access_payload = {
            'user_id': user.id,
            'userid': getattr(user, 'userid', ''),
            'role': getattr(user, 'role', ''),
            'exp': now + timedelta(hours=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'iat': now,
            'type': 'access'
        }

        # 刷新令牌载荷
        refresh_payload = {
            'user_id': user.id,
            'exp': now + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'iat': now,
            'type': 'refresh'
        }

        # 生成令牌
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME * 3600  # 转换为秒
        }

    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # 检查令牌类型
            if payload.get('type') != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """使用刷新令牌生成新的访问令牌"""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get('type') != 'refresh':
                return None

            # 获取用户信息
            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                user = User.objects.get(id=payload['user_id'], is_active=True)
                return JWTUtils.generate_tokens(user)
            except User.DoesNotExist:
                return None

        except jwt.InvalidTokenError:
            return None


# 创建全局实例
jwt_utils = JWTUtils()