"""
Main URL configuration for users app.
"""
from django.urls import path, include
from .urls import user as user_urls

app_name = 'users'

urlpatterns = [
    path('', include(user_urls)),
]