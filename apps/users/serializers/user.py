"""
Serializers for simplified User model and UserActivity model.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError
from ..models import User, UserActivity
from apps.common.utils.validators import validate_password_strength


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - read-only operations."""

    class Meta:
        model = User
        fields = [
            'id', 'userid', 'role', 'is_active', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['userid', 'password', 'password_confirm', 'role']

    def validate_userid(self, value):
        """Validate userid uniqueness and format."""
        if User.objects.filter(userid=value).exists():
            raise serializers.ValidationError("用户ID已存在")
        if len(value) < 3:
            raise serializers.ValidationError("用户ID长度不能少于3个字符")
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("用户ID只能包含字母、数字、下划线和横线")
        return value

    def validate_password(self, value):
        """Validate password strength."""
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")
        return attrs

    def create(self, validated_data):
        """Create user with encrypted password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = ['role', 'current_password', 'new_password']

    def validate_new_password(self, value):
        """Validate new password strength."""
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        """Validate password change if requested."""
        new_password = attrs.get('new_password')
        current_password = attrs.get('current_password')

        if new_password and not current_password:
            raise serializers.ValidationError("修改密码需要提供当前密码")

        if current_password and not new_password:
            raise serializers.ValidationError("提供当前密码时需要设置新密码")

        return attrs

    def update(self, instance, validated_data):
        """Update user with optional password change."""
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)

        # Handle password change
        if current_password and new_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError("当前密码不正确")
            instance.set_password(new_password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    userid = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        """Validate login credentials."""
        userid = attrs.get('userid')
        password = attrs.get('password')

        if not userid or not password:
            raise serializers.ValidationError("必须提供用户ID和密码")

        try:
            user = User.objects.get(userid=userid)
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在")

        if not user.check_password(password):
            raise serializers.ValidationError("密码错误")

        if not user.is_active:
            raise serializers.ValidationError("用户账户已被停用")

        attrs['user'] = user
        return attrs


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model."""
    userid = serializers.CharField(source='user.userid', read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            'id', 'userid', 'action', 'ip_address', 'user_agent',
            'success', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
    new_password_confirm = serializers.CharField()

    def validate_new_password(self, value):
        """Validate new password strength."""
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        """Validate password change."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("两次输入的新密码不一致")
        return attrs


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user role (admin only)."""

    class Meta:
        model = User
        fields = ['role']

    def validate_role(self, value):
        """Validate role value."""
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"无效的角色，可选值：{valid_roles}")
        return value


class UserStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user status (admin only)."""

    class Meta:
        model = User
        fields = ['is_active']