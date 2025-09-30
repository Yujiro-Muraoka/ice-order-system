"""
API URLs設定
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRFルーターの設定
router = DefaultRouter()
router.register(r'food-orders', views.FoodOrderViewSet)
router.register(r'ice-orders', views.IceOrderViewSet)
router.register(r'shavedice-orders', views.ShavedIceOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='api_health_check'),
]