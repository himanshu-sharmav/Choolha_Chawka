from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationLogViewSet

router = DefaultRouter()
router.register('logs', NotificationLogViewSet, basename='notification-logs')

urlpatterns = [
    path('', include(router.urls)),
]
