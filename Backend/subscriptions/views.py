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
        return Subscription.objects.select_related(
            'plan', 'user'
        ).filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
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

class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'mess_owner':
            # Mess owners can see all leaves with proper joins
            return Leave.objects.select_related(
                'subscription', 'subscription__user', 'subscription__plan', 'reviewed_by'
            ).all()
        else:
            # Regular users see only their own leaves
            return Leave.objects.select_related(
                'subscription', 'subscription__plan', 'reviewed_by'
            ).filter(subscription__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveCreateSerializer
        elif self.request.user.user_type == 'mess_owner' and self.action == 'list':
            return LeaveAdminSerializer
        return LeaveSerializer
    
    def create(self, request, *args, **kwargs):
        # Only customers can create leave requests
        if request.user.user_type not in ['student', 'regular']:
            return Response({
                'success': False,
                'message': 'Only customers can create leave requests'
            }, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()
        
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
