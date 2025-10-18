"""
URL configuration for UserService microservice.

API-only user management service endpoints.
"""
import datetime

from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for microservice monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'service': settings.SERVICE_NAME,
        'version': settings.SERVICE_VERSION,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

urlpatterns = [
    # Health and info endpoints
    path('health/', health_check, name='health_check'),

    # API endpoints
    path('api/v1/', include('apps.users.urls')),

    # Admin disabled in production for microservice
    # path('admin/', admin.site.urls),
]

# API documentation endpoint (if drf_yasg is installed)
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework.permissions import AllowAny

    schema_view = get_schema_view(
        openapi.Info(
            title="User Service API",
            default_version=settings.SERVICE_VERSION,
            description="User management microservice API",
            terms_of_service="https://example.com/terms/",
            contact=openapi.Contact(email="api@example.com"),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=[AllowAny],
    )

    urlpatterns += [
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
except ImportError:
    # drf_yasg not installed, skip API documentation
    pass
