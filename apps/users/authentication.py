"""
JWT认证模块
提供基于JWT的用户认证功能
"""

import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """JWT认证类"""

    def authenticate(self, request):
        """验证JWT令牌"""
        # 从请求头获取令牌
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # 解码JWT令牌
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # 检查令牌有效期
            if self.is_token_expired(payload):
                raise AuthenticationFailed('令牌已过期')

            # 获取用户
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('无效的令牌')

            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('用户不存在')

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('令牌已过期')
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的JWT令牌: {e}")
            raise AuthenticationFailed('无效的令牌')
        except Exception as e:
            logger.error(f"JWT认证过程中发生错误: {e}")
            raise AuthenticationFailed('认证失败')

    def is_token_expired(self, payload):
        """检查令牌是否过期"""
        exp = payload.get('exp')
        if not exp:
            return True

        return datetime.fromtimestamp(exp) < datetime.now()

    def generate_token(self, user):
        """为用户生成JWT令牌"""
        access_payload = {
            'user_id': user.id,
            'userid': getattr(user, 'userid', ''),
            'role': getattr(user, 'role', ''),
            'exp': datetime.now() + timedelta(hours=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'iat': datetime.now(),
            'type': 'access'
        }

        refresh_payload = {
            'user_id': user.id,
            'exp': datetime.now() + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'iat': datetime.now(),
            'type': 'refresh'
        }

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
            'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME * 3600
        }

    def refresh_token(self, refresh_token):
        """刷新访问令牌"""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get('type') != 'refresh':
                raise AuthenticationFailed('无效的刷新令牌')

            user_id = payload.get('user_id')
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('用户不存在')

            return self.generate_token(user)

        except jwt.InvalidTokenError:
            raise AuthenticationFailed('无效的刷新令牌')