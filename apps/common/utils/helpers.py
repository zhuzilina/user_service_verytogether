"""
Helper functions for UserService microservice.
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone


def generate_user_id():
    """
    Generate a unique user ID for external systems.
    """
    return f"user_{uuid.uuid4().hex[:12]}"


def generate_verification_token():
    """
    Generate a secure verification token for email verification.
    """
    return secrets.token_urlsafe(32)


def generate_password_reset_token():
    """
    Generate a secure password reset token.
    """
    return secrets.token_urlsafe(32)


def hash_password(password, salt=None):
    """
    Hash password with salt using SHA-256.
    Note: Django's built-in password hashing is recommended for production.
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Combine password and salt
    password_salt = (password + salt).encode('utf-8')

    # Hash with SHA-256
    hashed = hashlib.sha256(password_salt).hexdigest()

    return f"sha256${salt}${hashed}"


def verify_password(password, hashed_password):
    """
    Verify password against hashed password.
    """
    try:
        algorithm, salt, hash_value = hashed_password.split('$')

        if algorithm != 'sha256':
            return False

        # Hash the provided password with the same salt
        password_salt = (password + salt).encode('utf-8')
        computed_hash = hashlib.sha256(password_salt).hexdigest()

        return secrets.compare_digest(computed_hash, hash_value)
    except (ValueError, AttributeError):
        return False


def format_user_data(user, include_sensitive=False):
    """
    Format user data for API responses.
    """
    data = {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'avatar_url': user.avatar_url,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat(),
    }

    if include_sensitive:
        data.update({
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'last_login_ip': user.last_login_ip,
            'external_id': user.external_id,
            'source': user.source,
        })

    return data


def calculate_user_age(date_of_birth):
    """
    Calculate user's age from date of birth.
    """
    if not date_of_birth:
        return None

    today = timezone.now().date()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age


def is_email_verification_required(user):
    """
    Check if email verification is required for the user.
    """
    return not user.is_verified and user.email


def get_user_permissions(user):
    """
    Get user's permissions based on roles and groups.
    """
    permissions = set()

    if user.is_superuser:
        permissions.add('admin')
        permissions.add('all_users')

    if user.is_staff:
        permissions.add('staff')

    # Add user-specific permissions
    permissions.add('own_profile')
    permissions.add('own_activities')

    return list(permissions)


def sanitize_user_input(data):
    """
    Sanitize user input to prevent injection attacks.
    """
    if isinstance(data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
        sanitized = data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()

    elif isinstance(data, dict):
        return {key: sanitize_user_input(value) for key, value in data.items()}

    elif isinstance(data, list):
        return [sanitize_user_input(item) for item in data]

    return data


def paginate_queryset(queryset, page, page_size=20):
    """
    Paginate queryset and return paginated data.
    """
    start = (page - 1) * page_size
    end = start + page_size

    total = queryset.count()
    items = queryset[start:end]

    return {
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size,
            'has_next': end < total,
            'has_previous': page > 1,
        }
    }


def create_user_activity(user, action, description='', request=None):
    """
    Create a user activity record.
    """
    from apps.users.models import UserActivity

    ip_address = None
    user_agent = ''

    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    return UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_valid_uuid(uuid_string):
    """
    Check if a string is a valid UUID.
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def format_api_response(data=None, message='', status='success', code=200):
    """
    Format API response in consistent structure.
    """
    response = {
        'status': status,
        'code': code,
        'message': message,
    }

    if data is not None:
        response['data'] = data

    return response


def cache_user_data(user_id, data, timeout=300):
    """
    Cache user data for performance.
    """
    from django.core.cache import cache
    cache_key = f'user_data_{user_id}'
    cache.set(cache_key, data, timeout)


def get_cached_user_data(user_id):
    """
    Get cached user data.
    """
    from django.core.cache import cache
    cache_key = f'user_data_{user_id}'
    return cache.get(cache_key)


def invalidate_user_cache(user_id):
    """
    Invalidate cached user data.
    """
    from django.core.cache import cache
    cache_key = f'user_data_{user_id}'
    cache.delete(cache_key)