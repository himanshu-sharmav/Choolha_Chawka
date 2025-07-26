from rest_framework import serializers
from .models import Plan, Subscription, Leave
from django.utils import timezone

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'code', 'name', 'description', 'service_type', 'base_price', 
                  'included_meals', 'can_add_breakfast', 'breakfast_addon_price', 
                  'duration_days', 'is_active']

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['plan', 'breakfast_included']
    
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
            # subscription_type=plan.service_type,
            status='PENDING_PAYMENT'
        )
        
        return subscription
    
class SubscriptionBasicSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'breakfast_included', 'base_price', 'breakfast_addon_price',
                  'total_paid', 'start_date', 'base_end_date', 
                  'adjusted_end_date', 'leave_days', 'status', 'cancelled_at',
                  'days_remaining', 'created_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'breakfast_included', 'base_price', 'breakfast_addon_price',
                  'total_paid', 'start_date', 'base_end_date', 
                  'adjusted_end_date', 'leave_days', 'status', 'cancelled_at',
                  'days_remaining', 'is_active', 'created_at']
        read_only_fields = ['id', 'base_price', 'breakfast_addon_price', 'total_paid',
                           'start_date', 'base_end_date', 
                           'adjusted_end_date', 'leave_days', 'cancelled_at', 'created_at']
    
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
        return obj.subscription.user.get_full_name() or obj.subscription.user.username
    
    def get_subscription_plan(self, obj):
        return obj.subscription.plan.name
    
    def get_user_phone(self, obj):
        return obj.subscription.user.phone
