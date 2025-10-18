"""
Custom exception handlers for consistent API responses.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent API error responses.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # If DRF didn't handle the exception, create a custom response
    if response is None:
        if isinstance(exc, Http404):
            response = Response(
                {
                    'error': 'Not Found',
                    'message': 'The requested resource was not found.',
                    'code': 'not_found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {
                    'error': 'Permission Denied',
                    'message': 'You do not have permission to perform this action.',
                    'code': 'permission_denied'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, ValidationError):
            response = Response(
                {
                    'error': 'Validation Error',
                    'message': str(exc),
                    'code': 'validation_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Log unexpected errors
            logger.error(f'Unhandled exception: {exc}', exc_info=True)
            response = Response(
                {
                    'error': 'Internal Server Error',
                    'message': 'An unexpected error occurred.',
                    'code': 'internal_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Enhance existing DRF responses with microservice-specific format
    if response is not None:
        custom_response_data = {
            'error': response.data.get('detail', 'Error occurred'),
            'code': getattr(exc, 'default_code', 'error'),
        }

        # Add field-specific errors for validation errors
        if hasattr(response.data, 'items'):
            if 'non_field_errors' in response.data:
                custom_response_data['message'] = response.data['non_field_errors'][0]
            elif any(key in response.data for key in ['email', 'username', 'password']):
                custom_response_data['field_errors'] = {
                    field: errors for field, errors in response.data.items()
                    if field != 'detail' and field != 'non_field_errors'
                }
                custom_response_data['message'] = 'Validation failed for one or more fields.'
            else:
                custom_response_data['message'] = str(response.data)

        # Add request metadata for debugging
        if not response.status_code == 500:  # Don't expose internal details
            custom_response_data['request_id'] = getattr(context.get('request'), 'id', None)

        response.data = custom_response_data

    return response


class BaseServiceException(Exception):
    """
    Base exception class for microservice-specific errors.
    """
    def __init__(self, message, code=None, status_code=400):
        self.message = message
        self.code = code or 'service_error'
        self.status_code = status_code
        super().__init__(message)


class UserNotFoundException(BaseServiceException):
    """Raised when a user is not found."""
    def __init__(self, user_id=None):
        message = f"User with ID '{user_id}' not found." if user_id else "User not found."
        super().__init__(message, 'user_not_found', 404)


class UserAlreadyExistsException(BaseServiceException):
    """Raised when trying to create a user that already exists."""
    def __init__(self, field, value):
        message = f"User with {field} '{value}' already exists."
        super().__init__(message, 'user_already_exists', 409)


class InvalidTokenException(BaseServiceException):
    """Raised when authentication token is invalid."""
    def __init__(self):
        super().__init__(
            "Invalid authentication token.",
            'invalid_token',
            401
        )


class TokenExpiredException(BaseServiceException):
    """Raised when authentication token has expired."""
    def __init__(self):
        super().__init__(
            "Authentication token has expired.",
            'token_expired',
            401
        )


class PasswordMismatchException(BaseServiceException):
    """Raised when password confirmation doesn't match."""
    def __init__(self):
        super().__init__(
            "Passwords do not match.",
            'password_mismatch',
            400
        )


class WeakPasswordException(BaseServiceException):
    """Raised when password doesn't meet security requirements."""
    def __init__(self, message="Password does not meet security requirements."):
        super().__init__(message, 'weak_password', 400)


class AccountDisabledException(BaseServiceException):
    """Raised when trying to access a disabled account."""
    def __init__(self):
        super().__init__(
            "Account has been disabled.",
            'account_disabled',
            403
        )


class EmailNotVerifiedException(BaseServiceException):
    """Raised when trying to access an unverified account."""
    def __init__(self):
        super().__init__(
            "Email address has not been verified.",
            'email_not_verified',
            403
        )


class RateLimitExceededException(BaseServiceException):
    """Raised when API rate limit is exceeded."""
    def __init__(self, retry_after=None):
        message = "API rate limit exceeded. Please try again later."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
        super().__init__(message, 'rate_limit_exceeded', 429)
        self.retry_after = retry_after


class ServiceUnavailableException(BaseServiceException):
    """Raised when a dependent service is unavailable."""
    def __init__(self, service_name=None):
        message = "Service temporarily unavailable."
        if service_name:
            message = f"{service_name} service temporarily unavailable."
        super().__init__(message, 'service_unavailable', 503)