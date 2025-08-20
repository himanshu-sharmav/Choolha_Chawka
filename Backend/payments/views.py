from rest_framework import viewsets, status,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from core.permissions import IsCustomer, IsMessOwner
from .models import Payment, RazorpayOrder, RefundRequest
from .serializers import (
    PaymentSerializer, RazorpayOrderCreateSerializer, RazorpayOrderSerializer,
    PaymentVerificationSerializer, RefundRequestSerializer
)
from django.shortcuts import render
from .services import razorpay_service
from subscriptions.models import Subscription
from django.conf import settings
# from notifications.services import send_refund_processed_email, send_refund_rejected_email
from notifications.services import NotificationService
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.db.models import Sum, Count, Avg
from core.cache_service import cache_get, ListRetrieveCacheMixin

class PaymentViewSet(ListRetrieveCacheMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]  # Changed from IsCustomer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Payment.objects.none()
        return Payment.objects.select_related(
            'subscription', 'subscription__user', 'subscription__plan'
        ).filter(subscription__user=self.request.user)  # Fixed relationship
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Download payment receipt as HTML"""
        payment = self.get_object()
        
        # Ensure user owns this payment
        if payment.subscription.user != request.user:
            return Response({
                'error': 'You do not have permission to view this receipt.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate amount in rupees (convert from paise)
        amount_in_rupees = payment.amount / 100
        
        try:
            # Generate HTML receipt
            html_content = render_to_string('payments/receipt.html', {
                'payment': payment,
                'user': payment.subscription.user,
                'subscription': payment.subscription,
                'plan': payment.subscription.plan if payment.subscription else None,
                'amount_in_rupees': amount_in_rupees,
                'current_date': timezone.now(),
            })
            
            # Return HTML receipt
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'inline; filename="receipt_{payment.transaction_id}.html"'
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate receipt: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def receipt_pdf(self, request, pk=None):
        """Download payment receipt as PDF"""
        payment = self.get_object()
        
        # Ensure user owns this payment
        if payment.subscription.user != request.user:
            return Response({
                'error': 'You do not have permission to view this receipt.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Create PDF
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Header
            p.setFont("Helvetica-Bold", 20)
            p.drawString(100, height - 80, "🍽️ Mess Choolha Chowka")
            
            p.setFont("Helvetica", 12)
            p.drawString(100, height - 100, "Payment Receipt")
            
            # Receipt details
            y_position = height - 140
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y_position, f"Receipt ID: {payment.transaction_id}")
            y_position -= 30
            
            p.setFont("Helvetica", 12)
            p.drawString(100, y_position, f"Date: {payment.created_at.strftime('%B %d, %Y at %I:%M %p')}")
            y_position -= 20
            
            # Customer details
            user = payment.subscription.user
            p.drawString(100, y_position, f"Customer: {user.get_full_name() or user.username}")
            y_position -= 20
            p.drawString(100, y_position, f"Email: {user.email}")
            y_position -= 20
            p.drawString(100, y_position, f"Phone: {user.phone}")
            y_position -= 30
            
            # Subscription details
            if payment.subscription:
                p.setFont("Helvetica-Bold", 12)
                p.drawString(100, y_position, "Subscription Details:")
                y_position -= 20
                
                p.setFont("Helvetica", 12)
                p.drawString(100, y_position, f"Plan: {payment.subscription.plan.name}")
                y_position -= 20
                p.drawString(100, y_position, f"Service Type: {payment.subscription.plan.service_type.title()}")
                y_position -= 20
                p.drawString(100, y_position, f"Duration: {payment.subscription.plan.duration_days} days")
                y_position -= 30
            
            # Payment details
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y_position, "Payment Details:")
            y_position -= 20
            
            p.setFont("Helvetica", 12)
            p.drawString(100, y_position, f"Amount: ₹{payment.amount / 100:.2f}")
            y_position -= 20
            p.drawString(100, y_position, f"Payment Gateway: {payment.payment_gateway}")
            y_position -= 20
            p.drawString(100, y_position, f"Status: {payment.get_status_display()}")
            y_position -= 20
            p.drawString(100, y_position, f"Currency: {payment.currency}")
            y_position -= 40
            
            # Footer
            p.setFont("Helvetica", 10)
            p.drawString(100, 100, "Thank you for choosing Mess Choolha Chowka!")
            p.drawString(100, 85, "For support: support@choolhachowka.com")
            
            p.showPage()
            p.save()
            
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{payment.transaction_id}.pdf"'
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate PDF receipt: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @action(detail=False, methods=['get'], permission_classes=[])
    def test_page(self, request):
        """Render payment test page"""
        return render(request, 'payments/test_payment.html')

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
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
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

# payments/views.py


class AdminPaymentViewSet(ListRetrieveCacheMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for admin payment management"""
    serializer_class = PaymentSerializer
    permission_classes = [IsMessOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'payment_gateway', 'user', 'subscription__plan']
    search_fields = ['transaction_id', 'user__username', 'user__email', 'user__phone']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    @cache_get()
    def get_queryset(self):
        return Payment.objects.select_related(
            'user', 'subscription', 'subscription__plan'
        ).all()  # Admins can see all payments
    
    @action(detail=False, methods=['get'])
    @cache_get()
    def dashboard_stats(self, request):
        """Get payment dashboard statistics for admin"""
        all_payments = self.get_queryset()
        
        # Calculate statistics
        stats = {
            'total_payments': all_payments.count(),
            'successful_payments': all_payments.filter(status='completed').count(),
            'failed_payments': all_payments.filter(status='failed').count(),
            'pending_payments': all_payments.filter(status='pending').count(),
            'total_revenue': all_payments.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'today_revenue': all_payments.filter(
                status='completed',
                created_at__date=timezone.now().date()
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'this_month_revenue': all_payments.filter(
                status='completed',
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'average_payment': all_payments.filter(status='completed').aggregate(
                avg=Avg('amount')
            )['avg'] or 0,
        }
        
        # Convert amounts from paise to rupees
        for key in ['total_revenue', 'today_revenue', 'this_month_revenue', 'average_payment']:
            if stats[key]:
                stats[key] = stats[key] / 100
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    @cache_get()
    def recent_payments(self, request):
        """Get recent payments for admin"""
        recent = self.get_queryset()[:20]
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_get()
    def failed_payments(self, request):
        """Get failed payments for admin review"""
        failed = self.get_queryset().filter(status='failed')
        serializer = self.get_serializer(failed, many=True)
        return Response(serializer.data)


class RefundRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing refund requests (Manual refund processing)"""
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None

        if user_type == 'mess_owner':
            # Mess owners can see all refund requests
            return RefundRequest.objects.select_related(
                'subscription', 'subscription__plan', 'subscription__user', 
                'requested_by', 'original_payment'
            ).all()
        else:
            # Customers see only their own refund requests
            return RefundRequest.objects.select_related(
                'subscription', 'subscription__plan', 'requested_by', 'original_payment'
            ).filter(requested_by=user)

    
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
            NotificationService.send_refund_processed_email(refund_request.subscription.user, refund_request)
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
            NotificationService.send_refund_rejected_email(refund_request.subscription.user, refund_request)
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
        # refund_request.refund_transaction_id = request.data.get('transaction_id', f"manual_{timezone.now().timestamp()}")
        refund_request.admin_comment = request.data.get('admin_comment', 'Manually processed')
        refund_request.save()
        
         # 🔥 UPDATE SUBSCRIPTION REFUND STATUS
        if refund_request.subscription:
            refund_request.subscription.refund_status = 'PAID'
            refund_request.subscription.save(update_fields=['refund_status'])

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
