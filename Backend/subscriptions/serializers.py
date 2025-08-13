from rest_framework import serializers
from .models import Plan, Subscription, Leave
from django.utils import timezone
from django.db import models

class PlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['code', 'name', 'description', 'service_type', 'base_price', 
                  'included_meals', 'can_add_breakfast', 'breakfast_addon_price', 
                  'duration_days']
    
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

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'code', 'name', 'description', 'service_type', 'base_price', 
                  'included_meals', 'can_add_breakfast', 'breakfast_addon_price', 
                  'duration_days', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# subscriptions/serializers.py
class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['plan', 'breakfast_included']
    
    def validate(self, data):
        """Validate subscription creation rules"""
        user = self.context['request'].user
        plan = data['plan']
        
        # 0. Ensure user profile is complete and service type matches preference
        # Require profile completion for customers
        if getattr(user, 'user_type', None) in ['student', 'regular']:
            if getattr(user, 'status', '') != 'profile_complete':
                raise serializers.ValidationError(
                    'Please complete your profile before subscribing to a plan.'
                )

            # Enforce that only one of the flags is true in case of inconsistent data
            if getattr(user, 'is_tiffin_user', False) and getattr(user, 'is_mess_user', False):
                raise serializers.ValidationError(
                    'Your profile has both Tiffin and Mess selected. Please update your profile to select only one.'
                )

            # Match plan service type to user's selected preference
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
        
        if pending_subscriptions >= 2:  # Allow max 2 pending subscriptions
            raise serializers.ValidationError(
                "You can have maximum 2 pending subscriptions. "
                "Please complete payment for existing subscriptions first."
            )
        
        # # 3. Check for recent cancelled subscriptions (prevent abuse)
        # from django.utils import timezone
        # from datetime import timedelta
        
        # recent_cancelled = Subscription.objects.filter(
        #     user=user,
        #     plan=plan,
        #     status='CANCELLED',
        #     cancelled_at__gte=timezone.now() - timedelta(days=1)
        # ).exists()
        
        # if recent_cancelled:
        #     raise serializers.ValidationError(
        #         f"You recently cancelled a subscription for {plan.name}. "
        #         f"Please wait 24 hours before creating a new subscription for the same plan."
        #     )
        
        return data
    
    def create(self, validated_data):
        plan = validated_data['plan']
        breakfast_included = validated_data.get('breakfast_included', False)
        
        # Calculate pricing
        base_price = plan.base_price
        breakfast_addon_price = plan.breakfast_addon_price if breakfast_included else 0
        total_paid = base_price + breakfast_addon_price
        
        subscription = Subscription.objects.create(
            user=self.context['request'].user,
            plan=plan,
            breakfast_included=breakfast_included,
            base_price=base_price,
            breakfast_addon_price=breakfast_addon_price,
            total_paid=total_paid,
            status='PENDING_PAYMENT'
        )
        
        return subscription

    
class SubscriptionBasicSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField()
    refund_status = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'breakfast_included', 'base_price', 'breakfast_addon_price',
                  'total_paid', 'start_date', 'base_end_date', 
                  'adjusted_end_date', 'leave_days', 'status', 'cancelled_at',
                  'refund_status', 'days_remaining', 'created_at']
    
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
        fields = ['id', 'plan', 'breakfast_included', 'base_price', 'breakfast_addon_price',
                  'total_paid', 'start_date', 'base_end_date', 
                  'adjusted_end_date', 'leave_days', 'status', 'cancelled_at',
                  'refund_status', 'refund_info', 'days_remaining', 'is_active', 'created_at']
        read_only_fields = ['id', 'base_price', 'breakfast_addon_price', 'total_paid',
                           'start_date', 'base_end_date', 
                           'adjusted_end_date', 'leave_days', 'cancelled_at', 'created_at']
    
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
        return obj.status == 'ACTIVE' and timezone.now().date() <= obj.adjusted_end_date


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
