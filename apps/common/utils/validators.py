"""
Validation utilities for UserService microservice.
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email


def validate_email_domain(email):
    """
    Validate email domain against allowed domains or blacklist.
    """
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValidationError("Invalid email format")

    domain = email.split('@')[1].lower()

    # Add your domain validation logic here
    allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.com']
    blacklisted_domains = ['tempmail.com', 'throwaway.email']

    if domain in blacklisted_domains:
        raise ValidationError("Email domain is not allowed")

    if allowed_domains and domain not in allowed_domains:
        raise ValidationError("Email domain is not supported")


def validate_phone_number(phone):
    """
    Validate phone number format.
    """
    if not phone:
        return True  # Phone number is optional

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)

    # Check if it's a valid phone number length (10-15 digits)
    if not (10 <= len(digits_only) <= 15):
        raise ValidationError("Phone number must be between 10 and 15 digits")

    # Check if it starts with a valid country code (optional)
    if len(digits_only) > 10 and not digits_only.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
        raise ValidationError("Invalid country code")


def validate_username(username):
    """
    Validate username format.
    """
    if not username:
        raise ValidationError("Username is required")

    # Username should be 3-30 characters, alphanumeric + underscore + hyphen
    if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
        raise ValidationError(
            "Username must be 3-30 characters long and contain only letters, "
            "numbers, underscores, and hyphens"
        )

    # Username cannot start or end with underscore or hyphen
    if username.startswith(('_', '-')) or username.endswith(('_', '-')):
        raise ValidationError("Username cannot start or end with underscore or hyphen")

    # Username cannot contain consecutive underscores or hyphens
    if '__' in username or '--' in username:
        raise ValidationError("Username cannot contain consecutive underscores or hyphens")


def validate_password_strength(password):
    """
    Validate password strength requirements.
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValidationError("Password cannot be longer than 128 characters")

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")

    # Check for at least one digit
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character")


def validate_date_of_birth(date_of_birth):
    """
    Validate date of birth - must be between 13 and 120 years old.
    """
    from datetime import date
    today = date.today()

    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

    if age < 13:
        raise ValidationError("User must be at least 13 years old")

    if age > 120:
        raise ValidationError("Invalid date of birth")


def validate_avatar_url(url):
    """
    Validate avatar URL format and allowed domains.
    """
    if not url:
        return True  # Avatar URL is optional

    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        raise ValidationError("Invalid URL format")

    # Check for allowed image file extensions
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not any(url.lower().endswith(ext) for ext in allowed_extensions):
        raise ValidationError("Avatar URL must point to an image file")

    # Check if URL uses HTTPS in production
    if not url.startswith('https://'):
        raise ValidationError("Avatar URL must use HTTPS")