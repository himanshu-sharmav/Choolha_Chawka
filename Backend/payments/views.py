from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsCustomer
from .models import Payment, RazorpayOrder, RefundRequest
from .serializers import (
    PaymentSerializer, RazorpayOrderCreateSerializer, RazorpayOrderSerializer,
    PaymentVerificationSerializer, RefundRequestSerializer
)
from .services import razorpay_service
from subscriptions.models import Subscription
from django.conf import settings

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [IsCustomer]
    
    def get_queryset(self):
        return Payment.objects.select_related(
            'user', 'subscription', 'subscription__plan'
        ).filter(user=self.request.user)

class RazorpayOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Razorpay order management"""
    serializer_class = RazorpayOrderSerializer
    permission_classes = [IsCustomer]
    
    def get_queryset(self):
        return RazorpayOrder.objects.select_related(
            'subscription', 'subscription__plan', 'user'
        ).filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RazorpayOrderCreateSerializer
        return RazorpayOrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create Razorpay order for subscription payment"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        subscription = serializer.validated_data['subscription']
        
        try:
            order, razorpay_order = razorpay_service.create_order(subscription)
            
            response_data = {
                'order_id': order.order_id,
                'amount': order.amount,
                'currency': order.currency,
                'key': settings.RAZORPAY_KEY_ID,
                'subscription_id': subscription.id,
                'user': {
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'phone': request.user.phone,
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify Razorpay payment"""
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payment, subscription = razorpay_service.verify_payment(
                serializer.validated_data['razorpay_order_id'],
                serializer.validated_data['razorpay_payment_id'],
                serializer.validated_data['razorpay_signature']
            )
            
            return Response({
                'success': True,
                'message': 'Payment verified successfully',
                'payment_id': payment.id,
                'subscription_id': subscription.id,
                'subscription_status': subscription.status
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RefundRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing refund requests"""
    serializer_class = RefundRequestSerializer
    permission_classes = [IsCustomer]
    
    def get_queryset(self):
        return RefundRequest.objects.select_related(
            'subscription', 'subscription__plan', 'requested_by', 'original_payment'
        ).filter(requested_by=self.request.user)
