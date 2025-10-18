"""
Main URL configuration for users app.
"""
from django.urls import path, include
from .user import urlpatterns as user_patterns

app_name = 'users'

urlpatterns = [
    # Include user-specific URLs
    path('', include((user_patterns, 'users'), namespace='users')),
]