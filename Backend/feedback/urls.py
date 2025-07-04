from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackViewSet, AdminFeedbackViewSet

router = DefaultRouter()
router.register('feedback', FeedbackViewSet, basename='feedback')
router.register('admin/feedback', AdminFeedbackViewSet, basename='admin-feedback')

urlpatterns = [
    path('', include(router.urls)),
]
