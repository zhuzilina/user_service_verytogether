"""
URL configuration for users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import (
    UserViewSet, UserActivityViewSet,
    LoginView, LogoutView, RegisterView, ChangePasswordView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activities', UserActivityViewSet, basename='activity')

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # ViewSet URLs
    path('', include(router.urls)),
]
