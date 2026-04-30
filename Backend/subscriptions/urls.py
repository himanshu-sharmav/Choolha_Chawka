from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SubscriptionViewSet, LeaveViewSet, CartViewSet, BundleOrderViewSet

router = DefaultRouter()
router.register('plans', PlanViewSet)
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('leaves', LeaveViewSet, basename='leave')
router.register('cart', CartViewSet, basename='cart')
router.register('bundle-orders', BundleOrderViewSet, basename='bundle-order')

urlpatterns = [
    path('', include(router.urls)),
]
