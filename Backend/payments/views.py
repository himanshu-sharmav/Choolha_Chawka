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
from core.permissions import IsMessOwner, IsCustomer
from .services import razorpay_service
from subscriptions.models import Subscription
from django.conf import settings
from notifications.services import send_refund_processed_email,send_refund_rejected_email
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

class RefundRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing refund requests (Manual refund processing)"""
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'mess_owner':
            # Mess owners can see all refund requests
            return RefundRequest.objects.select_related(
                'subscription', 'subscription__plan', 'subscription__user', 
                'requested_by', 'original_payment'
            ).all()
        else:
            # Customers see only their own refund requests
            return RefundRequest.objects.select_related(
                'subscription', 'subscription__plan', 'requested_by', 'original_payment'
            ).filter(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def approve(self, request, pk=None):
        """Approve refund request for manual processing (Mess Owner only)"""
        refund_request = self.get_object()
        
        if refund_request.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending refund requests can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update refund request - Mark as approved for manual processing
        refund_request.status = 'APPROVED'
        refund_request.processed_at = timezone.now()
        refund_request.admin_comment = request.data.get('admin_comment', '')
        refund_request.save()
        
        # 🔥 NOTIFICATION FOR APPROVED REFUND (Manual processing)
        try:
            send_refund_processed_email(refund_request.subscription.user, refund_request)
        except Exception as e:
            print(f"Failed to send refund approved notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Refund approved for manual processing',
            'refund_request': RefundRequestSerializer(refund_request).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def reject(self, request, pk=None):
        """Reject refund request (Mess Owner only)"""
        refund_request = self.get_object()
        
        if refund_request.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending refund requests can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund_request.status = 'REJECTED'
        refund_request.processed_at = timezone.now()
        refund_request.admin_comment = request.data.get('admin_comment', '')
        refund_request.save()
        
        # 🔥 NOTIFICATION FOR REJECTED REFUND
        try:
            send_refund_rejected_email(refund_request.subscription.user, refund_request)
        except Exception as e:
            print(f"Failed to send refund rejected notification: {e}")
        
        return Response({
            'success': True,
            'message': 'Refund request rejected',
            'refund_request': RefundRequestSerializer(refund_request).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def mark_paid(self, request, pk=None):
        """Mark refund as manually paid (Mess Owner only)"""
        refund_request = self.get_object()
        
        if refund_request.status != 'APPROVED':
            return Response({
                'success': False,
                'message': 'Only approved refund requests can be marked as paid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund_request.status = 'PAID'
        refund_request.refund_transaction_id = request.data.get('transaction_id', f"manual_{timezone.now().timestamp()}")
        refund_request.admin_comment = request.data.get('admin_comment', 'Manually processed')
        refund_request.save()
        
        return Response({
            'success': True,
            'message': 'Refund marked as paid',
            'refund_request': RefundRequestSerializer(refund_request).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsMessOwner])
    def pending(self, request):
        """Get all pending refund requests (Mess Owner only)"""
        pending_refunds = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending_refunds, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsMessOwner])
    def approved(self, request):
        """Get all approved refund requests awaiting manual payment (Mess Owner only)"""
        approved_refunds = self.get_queryset().filter(status='APPROVED')
        serializer = self.get_serializer(approved_refunds, many=True)
        return Response(serializer.data)

