from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, RazorpayOrderViewSet, RefundRequestViewSet

router = DefaultRouter()
router.register('payments', PaymentViewSet, basename='payment')
router.register('orders', RazorpayOrderViewSet, basename='razorpay-order')
router.register('refunds', RefundRequestViewSet, basename='refund-request')


urlpatterns = [
    path('', include(router.urls)),
    path('test/', PaymentViewSet.as_view({'get': 'test_page'}), name='payment-test'),
]