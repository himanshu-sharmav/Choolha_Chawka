from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsMessOwner, IsCustomer
from .models import Plan, Subscription, Leave
from .serializers import (
    PlanSerializer,PlanCreateSerializer, SubscriptionSerializer, SubscriptionCreateSerializer,
    LeaveSerializer, LeaveCreateSerializer, LeaveAdminSerializer
)
from notifications.services import (
    send_subscription_created_email, send_leave_submitted_email,
    send_leave_approved_email, send_leave_rejected_email, send_new_user_joined_email,send_subscription_cancelled_email,send_subscription_renewed_email
)
from payments.models import RefundRequest,Payment

class PlanViewSet(viewsets.ModelViewSet):
    """ViewSet for listing, retrieving, creating, updating, and deleting plans"""
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action:
        - Read operations (list, retrieve): Public access
        - Write operations (create, update, delete): Mess owners only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = []  # No authentication required for viewing plans
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsMessOwner]  # Only mess owners can modify plans
        else:
            permission_classes = [IsAuthenticated]  # Default for other actions
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions and query parameters"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # For modification operations, show all plans (including inactive) to mess owners
            queryset = Plan.objects.all()
        else:
            # For read operations (including public access), only show active plans
            queryset = Plan.objects.filter(is_active=True)
        
        # Filter by service type if provided
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PlanCreateSerializer
        return PlanSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new plan (Mess Owner only)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Plan created successfully',
            'data': PlanSerializer(plan).data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a plan (Mess Owner only)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Plan updated successfully',
            'data': PlanSerializer(plan).data
        })
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update a plan (PATCH) (Mess Owner only)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a plan by setting is_active=False (Mess Owner only)"""
        instance = self.get_object()
        
        # Soft delete - set is_active to False instead of hard delete
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Plan deactivated successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsCustomer]  # Only customers can create subscriptions
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Subscription.objects.none()  # Return an empty queryset if not authenticated
        return Subscription.objects.select_related(
            'plan', 'user','refund_request'
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
        """Renew expired subscription by extending it"""
        subscription = self.get_object()

        # Only allow renewal for expired subscriptions
        if subscription.status != 'EXPIRED':
            return Response({
                'success': False,
                'message': 'Only expired subscriptions can be renewed. Active subscriptions will automatically continue until expiry.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate renewal amount (same as original subscription pricing)
        renewal_amount = subscription.base_price + subscription.breakfast_addon_price

        # Calculate new end date from today
        renewal_days = subscription.plan.duration_days
        today = timezone.now().date()
        new_end_date = today + timedelta(days=renewal_days)

        # Update the existing subscription
        subscription.adjusted_end_date = new_end_date
        subscription.total_paid += renewal_amount
        subscription.pending_payment_amount = renewal_amount
        subscription.status = 'PENDING_PAYMENT'  # Requires payment to reactivate

        subscription.save()

        # Send renewal payment notification
        try:
            send_subscription_renewed_email(request.user, subscription)
        except Exception as e:
            print(f"Failed to send renewal notification: {e}")

        return Response({
            'success': True,
            'message': f'Subscription renewal initiated for {renewal_days} days',
            'subscription_id': subscription.id,
            'new_end_date': subscription.adjusted_end_date,
            'renewal_amount': renewal_amount,
            'status': 'PENDING_PAYMENT', 
            'subscription': SubscriptionSerializer(subscription).data
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
