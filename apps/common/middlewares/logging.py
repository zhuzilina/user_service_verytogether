"""
Logging middleware for microservice request/response tracking.
"""
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('apps')


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests and responses with correlation IDs.
    """

    def process_request(self, request):
        """Add request ID and start time to request."""
        request.id = str(uuid.uuid4())
        request.start_time = time.time()

        # Log request details
        logger.info(
            f"Request started - {request.method} {request.path}",
            extra={
                'request_id': request.id,
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

    def process_response(self, request, response):
        """Log response details and timing."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            logger.info(
                f"Request completed - {request.method} {request.path} - {response.status_code}",
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'response_size': len(response.content) if hasattr(response, 'content') else 0,
                }
            )

            # Add correlation ID to response headers
            response['X-Request-ID'] = getattr(request, 'id', 'unknown')
            response['X-Response-Time-ms'] = str(round(duration * 1000, 2))

        return response

    def process_exception(self, request, exception):
        """Log exceptions."""
        logger.error(
            f"Request failed - {request.method} {request.path} - {type(exception).__name__}",
            extra={
                'request_id': getattr(request, 'id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            },
            exc_info=True
        )

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip