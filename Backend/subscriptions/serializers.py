from rest_framework import serializers
from .models import Plan, Subscription, Leave, Cart, CartItem, BundleOrder
from django.utils import timezone
from django.db import models
from decimal import Decimal


class PlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['code', 'name', 'description', 'service_type', 'base_price', 
                  'included_meals', 'duration_days', 'min_duration_days', 
                  'max_duration_days', 'allow_custom_duration', 'daily_rate_override']
    
    def validate_code(self, value):
        """Ensure plan code is unique"""
        if Plan.objects.filter(code=value).exists():
            raise serializers.ValidationError("Plan with this code already exists")
        return value
    
    def validate_base_price(self, value):
        """Ensure base price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0")
        return value
    
    def validate_duration_days(self, value):
        """Ensure duration is reasonable"""
        if value <= 0 or value > 365:
            raise serializers.ValidationError("Duration must be between 1 and 365 days")
        return value
    
    def validate(self, data):
        """Validate min/max duration constraints"""
        min_days = data.get('min_duration_days', 7)
        max_days = data.get('max_duration_days', 90)
        if min_days > max_days:
            raise serializers.ValidationError(
                "Minimum duration cannot be greater than maximum duration"
            )
        return data


class PlanSerializer(serializers.ModelSerializer):
    daily_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = ['id', 'code', 'name', 'description', 'service_type', 'base_price', 
                  'included_meals', 'duration_days', 'min_duration_days', 
                  'max_duration_days', 'allow_custom_duration', 'daily_rate',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_daily_rate(self, obj):
        return float(obj.get_daily_rate())


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    duration_days = serializers.IntegerField(required=False, default=None)
    
    class Meta:
        model = Subscription
        fields = ['plan', 'duration_days']
    
    def validate(self, data):
        """Validate subscription creation rules"""
        user = self.context['request'].user
        plan = data['plan']
        duration_days = data.get('duration_days') or plan.duration_days
        
        # Validate custom duration if provided
        if not plan.validate_duration(duration_days):
            raise serializers.ValidationError(
                f"Duration must be between {plan.min_duration_days} and {plan.max_duration_days} days"
            )
        
        data['duration_days'] = duration_days
        
        # 0. Ensure user profile is complete and service type matches preference
        if getattr(user, 'user_type', None) in ['student', 'regular']:
            if getattr(user, 'status', '') != 'profile_complete':
                raise serializers.ValidationError(
                    'Please complete your profile before subscribing to a plan.'
                )

            if getattr(user, 'is_tiffin_user', False) and getattr(user, 'is_mess_user', False):
                raise serializers.ValidationError(
                    'Your profile has both Tiffin and Mess selected. Please update your profile to select only one.'
                )

            if plan.service_type == 'tiffin' and not getattr(user, 'is_tiffin_user', False):
                raise serializers.ValidationError(
                    'You have not selected Tiffin service in your profile. Update your profile to subscribe to Tiffin plans.'
                )
            if plan.service_type == 'mess' and not getattr(user, 'is_mess_user', False):
                raise serializers.ValidationError(
                    'You have not selected Mess service in your profile. Update your profile to subscribe to Mess plans.'
                )

        # 1. Prevent multiple active subscriptions for same plan
        existing_active = Subscription.objects.filter(
            user=user,
            plan=plan,
            status__in=['ACTIVE', 'PENDING_PAYMENT']
        ).exists()
        
        if existing_active:
            raise serializers.ValidationError(
                f"You already have an active subscription for {plan.name}. "
                f"Please complete or cancel your existing subscription before creating a new one."
            )
        
        # 2. Prevent multiple pending subscriptions for same user
        pending_subscriptions = Subscription.objects.filter(
            user=user,
            status='PENDING_PAYMENT'
        ).count()
        
        if pending_subscriptions >= 2:
            raise serializers.ValidationError(
                "You can have maximum 2 pending subscriptions. "
                "Please complete payment for existing subscriptions first."
            )
        
        return data
    
    def create(self, validated_data):
        plan = validated_data['plan']
        duration_days = validated_data.get('duration_days', plan.duration_days)
        
        # Calculate pricing based on custom duration
        total_paid = plan.calculate_price_for_duration(duration_days)
        
        subscription = Subscription.objects.create(
            user=self.context['request'].user,
            plan=plan,
            base_price=plan.base_price,
            total_paid=total_paid,
            status='PENDING_PAYMENT'
        )
        
        return subscription

    
class SubscriptionBasicSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField()
    refund_status = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'base_price', 'total_paid', 'start_date', 
                  'base_end_date', 'adjusted_end_date', 'leave_days', 'status', 
                  'cancelled_at', 'refund_status', 'days_remaining', 'created_at']
    
    def get_refund_status(self, obj):
        """Get human-readable refund status"""
        try:
            refund_request = getattr(obj, 'refund_request', None)
            if refund_request:
                return refund_request.get_status_display()
            return 'No refund requested'
        except:
            return 'No refund requested'
    
    def get_days_remaining(self, obj):
        if obj.status != 'ACTIVE':
            return 0
        today = timezone.now().date()
        if today >= obj.adjusted_end_date:
            return 0
        return (obj.adjusted_end_date - today).days
     

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    refund_status = serializers.SerializerMethodField()
    refund_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'base_price', 'total_paid', 'start_date', 
                  'base_end_date', 'adjusted_end_date', 'leave_days', 'status', 
                  'cancelled_at', 'refund_status', 'refund_info', 'days_remaining', 
                  'is_active', 'created_at', 'bundle_order']
        read_only_fields = ['id', 'base_price', 'total_paid', 'start_date', 
                           'base_end_date', 'adjusted_end_date', 'leave_days', 
                           'cancelled_at', 'created_at']
    
    def get_refund_status(self, obj):
        """Get human-readable refund status"""
        try:
            refund_request = getattr(obj, 'refund_request', None)
            if refund_request:
                return refund_request.get_status_display()  # Returns "Pending", "Approved", etc.
            return 'No refund requested'
        except:
            return 'No refund requested'
    
    def get_refund_info(self, obj):
        """Get detailed refund information"""
        try:
            refund_request = getattr(obj, 'refund_request', None)
            if refund_request:
                return {
                    'id': refund_request.id,
                    'amount': refund_request.amount,  # Convert from paise to rupees
                    'status': refund_request.status,
                    'status_display': refund_request.get_status_display(),
                    'requested_at': refund_request.requested_at,
                    'processed_at': refund_request.processed_at,
                    'admin_comment': refund_request.admin_comment,
                    'requested_by': refund_request.requested_by.username if refund_request.requested_by else None
                }
            return None
        except:
            return None
    
    def get_days_remaining(self, obj):
        if obj.status != 'ACTIVE':
            return 0
        today = timezone.now().date()
        if today >= obj.adjusted_end_date:
            return 0
        return (obj.adjusted_end_date - today).days
    
    def get_is_active(self, obj):
        return obj.status == 'ACTIVE' and timezone.now().date() < obj.adjusted_end_date


class LeaveCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ['subscription', 'leave_start_date', 'leave_end_date', 'reason']
    
    def validate(self, data):
        subscription = data['subscription']
        leave_start_date = data['leave_start_date']
        leave_end_date = data['leave_end_date']
        user = self.context['request'].user
        
        # Validate subscription belongs to user
        if subscription.user != self.context['request'].user:
            raise serializers.ValidationError("You can only request leave for your own subscriptions")
        
        # Validate subscription is active
        if subscription.status != 'ACTIVE':
            raise serializers.ValidationError("Can only request leave for active subscriptions")
        
        # Validate dates
        if leave_start_date > leave_end_date:
            raise serializers.ValidationError("Start date cannot be after end date")
        
        if leave_start_date < timezone.now().date():
            raise serializers.ValidationError("Cannot request leave for past dates")
        
        # Check if leave dates are within subscription period
        if leave_start_date > subscription.adjusted_end_date:
            raise serializers.ValidationError("Leave dates are outside subscription period")
        
        # Calculate duration
        duration = (leave_end_date - leave_start_date).days + 1
        
        # Validate duration (max 15 days per request)
        if duration > 15:
            raise serializers.ValidationError("Maximum 15 days leave can be requested at once")
        
        # NEW: Check for overlapping leaves
        overlapping_leaves = Leave.objects.filter(
            subscription__user=user,
            status__in=['PENDING', 'APPROVED']  # Only check active/pending leaves
        ).filter(
            # Check for date range overlap using Django Q objects
            models.Q(leave_start_date__lte=leave_end_date) & 
            models.Q(leave_end_date__gte=leave_start_date)
        )
        
        if overlapping_leaves.exists():
            existing_leave = overlapping_leaves.first()
            raise serializers.ValidationError(
                f"You already have a leave request from {existing_leave.leave_start_date} "
                f"to {existing_leave.leave_end_date} that overlaps with your requested dates. "
                f"Please cancel the existing leave or choose different dates."
            )
        existing_pending = Leave.objects.filter(
                subscription=subscription,
                status='PENDING'
            ).exists()
        if existing_pending:
                raise serializers.ValidationError(
                    "You already have a pending leave request for this subscription."
                )

        return data

class LeaveSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Leave
        fields = [
            'id', 'subscription', 'leave_start_date', 'leave_end_date', 
            'duration_days', 'reason', 'status', 'requested_at', 
            'reviewed_at', 'reviewed_by_name', 'admin_comment'
        ]
        read_only_fields = [
            'id', 'duration_days', 'status', 'requested_at', 
            'reviewed_at', 'admin_comment'
        ]
    
    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.get_full_name() if obj.reviewed_by else None


class LeaveAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin leave management"""
    subscription_user = serializers.SerializerMethodField()
    subscription_plan = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Leave
        fields = [
            'id', 'subscription_user', 'subscription_plan', 'user_phone',
            'leave_start_date', 'leave_end_date', 'duration_days', 'reason', 
            'status', 'requested_at', 'reviewed_at', 'admin_comment'
        ]
    
    def get_subscription_user(self, obj):
        """Return structured user name data"""
        user = obj.subscription.user
        return {
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': user.get_full_name() or user.username,
            'username': user.username
        }

    
    def get_subscription_plan(self, obj):
        return obj.subscription.plan.name
    
    def get_user_phone(self, obj):
        return obj.subscription.user.phone


class ModifySubscriptionDaysSerializer(serializers.Serializer):
    """Serializer for owner to modify subscription days"""
    days_to_add = serializers.IntegerField(
        required=True,
        help_text="Number of days to add (use negative value to remove days)"
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Reason for modifying subscription days"
    )
    
    def validate_days_to_add(self, value):
        """Validate days_to_add is within reasonable range"""
        if value == 0:
            raise serializers.ValidationError("days_to_add cannot be zero")
        if abs(value) > 365:
            raise serializers.ValidationError("Cannot modify by more than 365 days at once")
        return value


# ============== Cart Serializers ==============

class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items with calculated price"""
    plan = PlanSerializer(read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    daily_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    calculated_price = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'plan', 'plan_name', 'custom_duration_days', 'daily_rate', 
                  'calculated_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for user's cart with all items"""
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total(self, obj):
        return obj.get_total()
    
    def get_item_count(self, obj):
        return obj.get_item_count()


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding a plan to cart"""
    plan_id = serializers.IntegerField(required=True)
    duration_days = serializers.IntegerField(required=False, default=30)
    
    def validate_plan_id(self, value):
        """Validate plan exists and is active"""
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Plan not found or inactive")
        return value
    
    def validate(self, data):
        """Validate duration is within plan's allowed range"""
        plan = Plan.objects.get(id=data['plan_id'])
        duration = data.get('duration_days', plan.duration_days)
        
        if not plan.validate_duration(duration):
            raise serializers.ValidationError({
                'duration_days': f"Duration must be between {plan.min_duration_days} and {plan.max_duration_days} days"
            })
        
        data['plan'] = plan
        data['duration_days'] = duration
        return data


class UpdateDurationSerializer(serializers.Serializer):
    """Serializer for updating cart item duration"""
    duration_days = serializers.IntegerField(required=True, min_value=1)
    
    def validate_duration_days(self, value):
        """Basic validation - plan-specific validation done in view"""
        if value > 365:
            raise serializers.ValidationError("Duration cannot exceed 365 days")
        return value


class BundleOrderSerializer(serializers.ModelSerializer):
    """Serializer for bundle orders"""
    subscriptions = SubscriptionBasicSerializer(many=True, read_only=True)
    subscription_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BundleOrder
        fields = ['id', 'total_amount', 'status', 'razorpay_order_id', 
                  'razorpay_payment_id', 'subscriptions', 'subscription_count',
                  'created_at', 'paid_at']
        read_only_fields = ['id', 'created_at', 'paid_at']
    
    def get_subscription_count(self, obj):
        return obj.get_subscription_count()


class BundleOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for bundle order lists"""
    subscription_count = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = BundleOrder
        fields = ['id', 'user_info', 'total_amount', 'status', 
                  'subscription_count', 'created_at', 'paid_at']
    
    def get_subscription_count(self, obj):
        return obj.get_subscription_count()
    
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'phone': getattr(obj.user, 'phone', None)
        }
