from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsMessOwner, IsCustomer
from .models import Plan, Subscription, Leave
from .serializers import (
    PlanSerializer, SubscriptionSerializer, SubscriptionCreateSerializer,
    LeaveSerializer, LeaveCreateSerializer, LeaveAdminSerializer
)
from notifications.services import (
    send_subscription_created_email, send_leave_submitted_email,
    send_leave_approved_email, send_leave_rejected_email, send_new_user_joined_email,send_subscription_cancelled_email,send_subscription_renewed_email
)
from payments.models import RefundRequest,Payment

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving plans"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        return queryset

class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsCustomer]  # Only customers can create subscriptions
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Subscription.objects.none()  # Return an empty queryset if not authenticated
        return Subscription.objects.select_related(
            'plan', 'user'
        ).filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new subscription"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save(user=request.user)
        
        # 🔥 ADD NOTIFICATION HERE - After subscription creation
        try:
            send_subscription_created_email(request.user, subscription)
        except Exception as e:
            print(f"Failed to send subscription created email: {e}")
        
        return Response({
            'success': True,
            'message': 'Subscription created successfully',
            'data': SubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription and calculate refund"""
        subscription = self.get_object()
        
        if subscription.status != 'ACTIVE':
            return Response({
                'success': False,
                'message': 'Only active subscriptions can be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate refund
        refund_amount = subscription.calculate_refund()
        
        # Update subscription
        subscription.status = 'CANCELLED'
        subscription.cancelled_at = timezone.now()
        subscription.refund_amount_calculated = refund_amount
        subscription.refund_status = 'PENDING' if refund_amount > 0 else 'NOT_APPLICABLE'
        subscription.save()
         # 🔥 CREATE REFUND REQUEST IF ELIGIBLE
        if refund_amount > 0:
            
            # Get the original payment for this subscription
            # original_payment = subscription.refund_request.filter(status='SUCCESS').first()
            original_payment = Payment.objects.filter(
            subscription=subscription, 
            status='SUCCESS'
        ).first()
            
            if original_payment:
                refund_request = RefundRequest.objects.create(
                    subscription=subscription,
                    requested_by=request.user,
                    original_payment=original_payment,
                    amount=int(refund_amount ),  # Convert to paise
                    status='PENDING'
                )
        
        try:
            send_subscription_cancelled_email(request.user, subscription)
        except Exception as e:
            print(f"Failed to send subscription cancelled email: {e}")
        
        return Response({
            'success': True,
            'message': 'Subscription cancelled successfully',
            'refund_amount': refund_amount,
            'refund_status': subscription.refund_status
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's active subscription"""
        active_subscription = self.get_queryset().filter(status='ACTIVE').first()
        if active_subscription:
            serializer = self.get_serializer(active_subscription)
            return Response(serializer.data)
        
        return Response({
            'message': 'No active subscription found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew an expired or expiring subscription"""
        old_subscription = self.get_object()

        if old_subscription.status not in ['ACTIVE', 'EXPIRED']:
            return Response({
                'success': False,
                'message': 'Only active or expired subscriptions can be renewed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Determine start date for new subscription
        if old_subscription.status == 'ACTIVE':
            # Start after current subscription ends
            new_start_date = old_subscription.adjusted_end_date + timedelta(days=1)
        else:  # EXPIRED
            # Start immediately for expired subscriptions
            new_start_date = timezone.now().date()

        # Calculate total amount (same as old subscription)
        total_amount = old_subscription.base_price + old_subscription.breakfast_addon_price

        # Create new subscription with all required fields
        new_subscription = Subscription.objects.create(
            user=old_subscription.user,
            plan=old_subscription.plan,
            breakfast_included=old_subscription.breakfast_included,
            base_price=old_subscription.base_price,  # Use old subscription's price, not plan's
            breakfast_addon_price=old_subscription.breakfast_addon_price,  # Use old subscription's addon price
            total_paid=total_amount,  # ← FIX: Set the required total_paid field
            # subscription_type=old_subscription.subscription_type,
            start_date=new_start_date,
            status='PENDING_PAYMENT'  # Explicitly set status
        )


        # Mark old subscription as renewed
        old_subscription.status = 'RENEWED'
        old_subscription.save()

        # Send renewal notification
        try:
            send_subscription_renewed_email(request.user, old_subscription, new_subscription)
        except Exception as e:
            print(f"Failed to send renewal notification: {e}")

        return Response({
            'success': True,
            'message': 'Subscription renewed successfully',
            'old_subscription_id': old_subscription.id,
            'new_subscription_id': new_subscription.id,
            'new_subscription': SubscriptionSerializer(new_subscription).data
        })


class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Leave.objects.none()  # Return an empty queryset if not authenticated
        if self.request.user.user_type == 'mess_owner':
            return Leave.objects.select_related(
                'subscription', 'subscription__user', 'subscription__plan', 'reviewed_by'
            ).all()
        else:
            return Leave.objects.select_related(
                'subscription', 'subscription__plan', 'reviewed_by'
            ).filter(subscription__user=self.request.user)
    
    def get_serializer_class(self):
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None

        if self.action == 'create':
            return LeaveCreateSerializer
        elif user_type == 'mess_owner' and self.action == 'list':
            return LeaveAdminSerializer
        return LeaveSerializer

    
    def create(self, request, *args, **kwargs):
     user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
    
     # Only customers can create leave requests
     if user_type not in ['student', 'regular']:
         return Response({
             'success': False,
             'message': 'Only customers can create leave requests'
         }, status=status.HTTP_403_FORBIDDEN)
         
     serializer = self.get_serializer(data=request.data)
     serializer.is_valid(raise_exception=True)
     leave = serializer.save()
     
     try:
         send_leave_submitted_email(request.user, leave)
     except Exception as e:
         print(f"Failed to send leave submitted email: {e}")
    
     return Response({
         'success': True,
         'message': f'Leave request submitted for {leave.duration_days} days. Awaiting admin approval.',
         'status': leave.status,
         'leave_id': leave.id
     }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def approve(self, request, pk=None):
        """Approve leave request (Mess Owner only)"""
        leave = self.get_object()
        comment = request.data.get('admin_comment', '')
        
        if leave.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending leaves can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leave.approve_leave(request.user, comment)
        
        try:
            send_leave_approved_email(leave.subscription.user, leave)
        except Exception as e:
            print(f"Failed to send leave approved email: {e}")

        return Response({
            'success': True,
            'message': f'Leave approved for {leave.duration_days} days',
            'leave': LeaveSerializer(leave).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def reject(self, request, pk=None):
        """Reject leave request (Mess Owner only)"""
        leave = self.get_object()
        comment = request.data.get('admin_comment', '')
        
        if leave.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending leaves can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        leave.reject_leave(request.user, comment)
        
        try:
            send_leave_rejected_email(leave.subscription.user, leave)
        except Exception as e:
            print(f"Failed to send leave rejected email: {e}")

        return Response({
            'success': True,
            'message': 'Leave request rejected',
            'leave': LeaveSerializer(leave).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsMessOwner])
    def pending(self, request):
        """Get all pending leave requests (Mess Owner only)"""
        pending_leaves = self.get_queryset().filter(status='PENDING')
        serializer = LeaveAdminSerializer(pending_leaves, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsMessOwner])
    def dashboard_stats(self, request):
        """Get dashboard statistics (Mess Owner only)"""
        queryset = self.get_queryset()
        stats = {
            'pending_leaves': queryset.filter(status='PENDING').count(),
            'approved_leaves_today': queryset.filter(
                status='APPROVED',
                reviewed_at__date=timezone.now().date()
            ).count(),
            'total_leaves_this_month': queryset.filter(
                requested_at__month=timezone.now().month,
                requested_at__year=timezone.now().year
            ).count(),
        }
        return Response(stats)
