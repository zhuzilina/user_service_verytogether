"""
Security middleware for microservice API protection.
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger('apps')


class SecurityMiddleware(MiddlewareMixin):
    """
    Security middleware to add security headers and validate requests.
    """

    def process_response(self, request, response):
        """Add security headers to response."""
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # API-specific headers
        response['X-API-Version'] = 'v1'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

    def process_request(self, request):
        """Validate request for security issues."""
        # Check for suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_patterns = ['bot', 'crawler', 'scanner', 'exploit']

        if any(pattern in user_agent for pattern in suspicious_patterns):
            logger.warning(
                f"Suspicious user agent detected: {user_agent}",
                extra={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': user_agent,
                    'path': request.path,
                }
            )

        # Validate content type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type or ''
            if not content_type.startswith('application/json') and not content_type.startswith('multipart/form-data'):
                logger.warning(
                    f"Invalid content type for {request.method}: {content_type}",
                    extra={
                        'ip_address': self.get_client_ip(request),
                        'method': request.method,
                        'content_type': content_type,
                        'path': request.path,
                    }
                )

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip