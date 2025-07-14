from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SubscriptionViewSet, LeaveViewSet

router = DefaultRouter()
router.register('plans', PlanViewSet,basename='plan')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('leaves', LeaveViewSet, basename='leave')

urlpatterns = [
    path('', include(router.urls)),
]
