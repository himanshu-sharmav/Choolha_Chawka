from django.urls import path, include
from rest_framework.routers import DefaultRouter
from subscriptions.views import LeaveViewSet

# Mess owner specific routes  
router = DefaultRouter()
router.register('leaves', LeaveViewSet, basename='owner-leaves')

urlpatterns = [
    path('', include(router.urls)),
]
