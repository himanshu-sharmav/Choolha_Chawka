from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from core.permissions import IsMessOwner, IsCustomer
from .models import Plan, Subscription, Leave, Cart, CartItem, BundleOrder
from .serializers import (
    PlanSerializer, PlanCreateSerializer, SubscriptionSerializer, SubscriptionCreateSerializer,
    LeaveSerializer, LeaveCreateSerializer, LeaveAdminSerializer, ModifySubscriptionDaysSerializer,
    CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateDurationSerializer,
    BundleOrderSerializer, BundleOrderListSerializer
)
from .services import CartService, CheckoutService, PricingEngine
from notifications.services import (
    send_subscription_created_email, send_leave_submitted_email,
    send_leave_approved_email, send_leave_rejected_email, send_new_user_joined_email,
    send_subscription_cancelled_email, send_subscription_renewed_email
)
from payments.models import RefundRequest, Payment
from core.cache_service import cache_get, ListRetrieveCacheMixin

class PlanViewSet(ListRetrieveCacheMixin, viewsets.ModelViewSet):
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


class SubscriptionViewSet(ListRetrieveCacheMixin, viewsets.ModelViewSet):
    """ViewSet for managing user subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsCustomer]  # Only customers can create subscriptions
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Subscription.objects.none()  # Return an empty queryset if not authenticated
        
        # Allow mess owners to access all subscriptions for modify_days action
        if self.action == 'modify_days' and self.request.user.user_type == 'mess_owner':
            return Subscription.objects.select_related('plan', 'user', 'refund_request')
        
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
    @cache_get()
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
        renewal_amount = subscription.base_price

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

    @action(detail=True, methods=['post'], permission_classes=[IsMessOwner])
    def modify_days(self, request, pk=None):
        """
        Owner endpoint to modify subscription days for any user.
        
        Allows mess owners to add or remove days from a user's subscription.
        Useful for:
        - Compensating users for service issues
        - Adjusting for holidays or closures
        - Manual corrections
        
        Request body:
        {
            "days_to_add": 5,  // Use negative value to remove days (e.g., -3)
            "reason": "Compensation for service disruption"  // Optional
        }
        """
        subscription = self.get_object()
        
        # Validate request data
        serializer = ModifySubscriptionDaysSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        days_to_add = serializer.validated_data['days_to_add']
        reason = serializer.validated_data.get('reason', '')
        
        # Store original values for logging
        original_end_date = subscription.adjusted_end_date
        original_status = subscription.status
        
        # Calculate new end date
        new_end_date = subscription.adjusted_end_date + timedelta(days=days_to_add)
        
        # Validate that new end date is not in the past
        today = timezone.now().date()
        if new_end_date < today:
            return Response({
                'success': False,
                'message': f'Cannot set end date to the past. New end date would be {new_end_date}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update subscription
        subscription.adjusted_end_date = new_end_date
        
        # If subscription was expired but now has future date, reactivate it
        status_changed = False
        if subscription.status == 'EXPIRED' and new_end_date >= today:
            subscription.status = 'ACTIVE'
            status_changed = True
        
        subscription.save()
        
        # Log the modification
        action_type = "added" if days_to_add > 0 else "removed"
        days_abs = abs(days_to_add)
        
        message = f'Successfully {action_type} {days_abs} day(s) to subscription for {subscription.user.username}'
        if status_changed:
            message += f' and reactivated subscription (was {original_status})'
        
        return Response({
            'success': True,
            'message': message,
            'subscription_id': subscription.id,
            'user': {
                'id': subscription.user.id,
                'username': subscription.user.username,
                'email': subscription.user.email,
                'phone': subscription.user.phone
            },
            'modification': {
                'original_end_date': original_end_date,
                'new_end_date': subscription.adjusted_end_date,
                'days_modified': days_to_add,
                'reason': reason,
                'modified_by': request.user.username,
                'modified_at': timezone.now()
            },
            'status': {
                'original': original_status,
                'current': subscription.status,
                'changed': status_changed
            },
            'subscription': SubscriptionSerializer(subscription).data
        })


class LeaveViewSet(ListRetrieveCacheMixin, viewsets.ModelViewSet):
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
    @cache_get()
    def pending(self, request):
        """Get all pending leave requests (Mess Owner only)"""
        pending_leaves = self.get_queryset().filter(status='PENDING')
        serializer = LeaveAdminSerializer(pending_leaves, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsMessOwner])
    @cache_get()
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


class CartViewSet(viewsets.ViewSet):
    """ViewSet for managing user's shopping cart"""
    permission_classes = [IsCustomer]
    
    def list(self, request):
        """Get current user's cart with all items"""
        cart = CartService.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """Add a plan to cart"""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            item = CartService.add_item(
                user=request.user,
                plan_id=serializer.validated_data['plan_id'],
                duration_days=serializer.validated_data['duration_days']
            )
            return Response({
                'success': True,
                'message': f"Added {item.plan.name} to cart",
                'item': CartItemSerializer(item).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'errors': e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='update')
    def update_duration(self, request, pk=None):
        """Update duration for a cart item"""
        serializer = UpdateDurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            item = CartService.update_item_duration(
                user=request.user,
                item_id=int(pk),
                duration_days=serializer.validated_data['duration_days']
            )
            return Response({
                'success': True,
                'message': f"Updated duration to {item.custom_duration_days} days",
                'item': CartItemSerializer(item).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'errors': e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='remove')
    def remove(self, request, pk=None):
        """Remove an item from cart"""
        deleted = CartService.remove_item(request.user, int(pk))
        if deleted:
            return Response({
                'success': True,
                'message': 'Item removed from cart'
            })
        return Response({
            'success': False,
            'message': 'Item not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart"""
        CartService.clear_cart(request.user)
        return Response({
            'success': True,
            'message': 'Cart cleared'
        })
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Initiate checkout and create Razorpay order"""
        cart = CartService.get_or_create_cart(request.user)
        
        try:
            bundle_order, razorpay_order = CheckoutService.create_razorpay_order(cart)
            return Response({
                'success': True,
                'bundle_order_id': bundle_order.id,
                'razorpay_order_id': razorpay_order['id'],
                'amount': bundle_order.total_amount,
                'currency': 'INR',
                'key_id': settings.RAZORPAY_KEY_ID
            })
        except Exception as e:
            return Response({
                'success': False,
                'errors': e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify payment and complete checkout"""
        bundle_order_id = request.data.get('bundle_order_id')
        payment_id = request.data.get('razorpay_payment_id')
        signature = request.data.get('razorpay_signature')
        
        if not all([bundle_order_id, payment_id, signature]):
            return Response({
                'success': False,
                'message': 'Missing required fields: bundle_order_id, razorpay_payment_id, razorpay_signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bundle_order = BundleOrder.objects.get(
                id=bundle_order_id, 
                user=request.user
            )
        except BundleOrder.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Bundle order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            subscriptions = CheckoutService.complete_checkout(
                bundle_order=bundle_order,
                payment_id=payment_id,
                signature=signature
            )
            
            # Send confirmation email
            try:
                from notifications.services import send_bundle_order_confirmation_email
                send_bundle_order_confirmation_email(request.user, bundle_order, subscriptions)
            except Exception as e:
                print(f"Failed to send bundle order confirmation email: {e}")
            
            return Response({
                'success': True,
                'message': f'Successfully subscribed to {len(subscriptions)} plan(s)',
                'bundle_order': BundleOrderSerializer(bundle_order).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'errors': e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BundleOrderViewSet(ListRetrieveCacheMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing bundle orders (Owner dashboard)"""
    permission_classes = [IsMessOwner]
    
    def get_queryset(self):
        queryset = BundleOrder.objects.select_related('user').prefetch_related(
            'subscriptions__plan'
        ).all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BundleOrderListSerializer
        return BundleOrderSerializer
    
    @action(detail=False, methods=['get'])
    @cache_get()
    def stats(self, request):
        """Get bundle order statistics"""
        from django.db.models import Sum, Avg, Count
        
        queryset = self.get_queryset()
        paid_orders = queryset.filter(status='PAID')
        
        stats = {
            'total_orders': queryset.count(),
            'paid_orders': paid_orders.count(),
            'total_revenue': paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_order_value': paid_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
            'orders_this_month': queryset.filter(
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).count(),
        }
        return Response(stats)
