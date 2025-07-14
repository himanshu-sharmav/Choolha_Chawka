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
    LeaveSerializer, LeaveCreateSerializer, LeaveAdminSerializer,
    PlanCreateUpdateSerializer
)
from notifications.services import (
    send_subscription_created_email, send_leave_submitted_email,
    send_leave_approved_email, send_leave_rejected_email, send_new_user_joined_email,
    send_subscription_cancelled_email, send_subscription_renewed_email
)
from payments.models import RefundRequest, Payment

class PlanViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for Plan management"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Plan.objects.none()
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None
        
        if user_type == 'mess_owner':
            return Plan.objects.all()
        elif user.is_authenticated:
            # Regular users can only see active plans
            return Plan.objects.filter(is_active=True)
        else:
            return Plan.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update', 'update']:
            return PlanCreateUpdateSerializer
        return PlanSerializer

    def create(self, request, *args, **kwargs):
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner':
            return Response({
                'success': False,
                'message': 'Only mess owners can create plans'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Plan created successfully',
            'data': PlanSerializer(plan).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner':
            return Response({
                'success': False,
                'message': 'Only mess owners can update plans'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner':
            return Response({
                'success': False,
                'message': 'Only mess owners can delete plans'
            }, status=status.HTTP_403_FORBIDDEN)
        
        plan = self.get_object()
        plan.delete()
        return Response({
            'success': True,
            'message': 'Plan deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class SubscriptionViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for Subscription management"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subscription.objects.none()
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None
        
        if user_type == 'mess_owner':
            return Subscription.objects.select_related('user', 'plan').all()
        elif user.is_authenticated:
            return Subscription.objects.select_related('plan').filter(user=user)
        else:
            return Subscription.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new subscription"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the user to the current user if not provided
        if 'user' not in serializer.validated_data:
            serializer.validated_data['user'] = request.user
        
        subscription = serializer.save()
        
        try:
            send_subscription_created_email(request.user, subscription)
        except Exception as e:
            print(f"Failed to send subscription created email: {e}")
        
        return Response({
            'success': True,
            'message': 'Subscription created successfully',
            'subscription_id': subscription.id,
            'data': SubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        # Only mess_owner can update subscriptions or users can update their own
        if user_type != 'mess_owner' and instance.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only update your own subscription'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Subscription updated successfully',
            'data': SubscriptionSerializer(subscription).data
        })

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner' and instance.user != request.user:
            return Response({
                'success': False,
                'message': 'You cannot delete this subscription'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        return Response({
            'success': True,
            'message': 'Subscription deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

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
        
        # Create refund request if eligible
        if refund_amount > 0:
            original_payment = Payment.objects.filter(
                subscription=subscription, 
                status='SUCCESS'
            ).first()
            
            if original_payment:
                RefundRequest.objects.create(
                    subscription=subscription,
                    requested_by=request.user,
                    original_payment=original_payment,
                    amount=int(refund_amount),
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
            new_start_date = old_subscription.adjusted_end_date + timedelta(days=1)
        else:
            new_start_date = timezone.now().date()

        # Calculate total amount (same as old subscription)
        total_amount = old_subscription.base_price + old_subscription.breakfast_addon_price

        # Create new subscription with all required fields
        new_subscription = Subscription.objects.create(
            user=old_subscription.user,
            plan=old_subscription.plan,
            breakfast_included=old_subscription.breakfast_included,
            base_price=old_subscription.base_price,
            breakfast_addon_price=old_subscription.breakfast_addon_price,
            total_paid=total_amount,
            subscription_type=old_subscription.subscription_type,
            start_date=new_start_date,
            status='PENDING_PAYMENT'
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

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate/deactivate subscription (mess_owner only)"""
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner':
            return Response({
                'success': False,
                'message': 'Only mess owners can activate/deactivate subscriptions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        subscription = self.get_object()
        subscription.is_active = not subscription.is_active
        subscription.save()
        
        return Response({
            'success': True,
            'message': f'Subscription {"activated" if subscription.is_active else "deactivated"} successfully',
            'is_active': subscription.is_active
        })

class LeaveViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for Leave management"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Leave.objects.none()
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None

        if user_type == 'mess_owner':
            return Leave.objects.select_related(
                'subscription', 'subscription__user', 'subscription__plan', 'reviewed_by'
            ).all()
        elif user.is_authenticated:
            return Leave.objects.select_related(
                'subscription', 'subscription__plan', 'reviewed_by'
            ).filter(subscription__user=user)
        else:
            return Leave.objects.none()
    
    def get_serializer_class(self):
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None

        if self.action == 'create':
            return LeaveCreateSerializer
        elif user_type == 'mess_owner' and self.action == 'list':
            return LeaveAdminSerializer
        elif self.action in ['update', 'partial_update']:
            return LeaveAdminSerializer if user_type == 'mess_owner' else LeaveSerializer
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
            'leave_id': leave.id,
            'data': LeaveSerializer(leave).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        # Only mess_owner can update leave requests or users can update their own pending requests
        if user_type != 'mess_owner' and (instance.subscription.user != request.user or instance.status != 'PENDING'):
            return Response({
                'success': False,
                'message': 'You can only update your own pending leave requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Leave request updated successfully',
            'data': LeaveSerializer(leave).data
        })

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        # Only mess_owner can delete leave requests or users can delete their own pending requests
        if user_type != 'mess_owner' and (instance.subscription.user != request.user or instance.status != 'PENDING'):
            return Response({
                'success': False,
                'message': 'You can only delete your own pending leave requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        return Response({
            'success': True,
            'message': 'Leave request deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

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
