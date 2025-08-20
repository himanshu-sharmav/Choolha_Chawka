from rest_framework import serializers
from .models import Payment, RazorpayOrder, RefundRequest
from subscriptions.serializers import SubscriptionSerializer

class AdminPaymentListSerializer(serializers.ModelSerializer):
    amount_inr = serializers.SerializerMethodField()
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_gateway', 'transaction_id',
            'amount', 'amount_inr', 'currency', 'status',
            'created_at', 'updated_at', 'user_first_name', 'user_last_name',
            'plan_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_amount_inr(self, obj):
        return obj.amount / 100

    def get_user_first_name(self, obj):
        return getattr(obj.user, 'first_name', '') or ''

    def get_user_last_name(self, obj):
        return getattr(obj.user, 'last_name', '') or ''

    def get_plan_name(self, obj):
        try:
            return obj.subscription.plan.name if obj.subscription and obj.subscription.plan else None
        except Exception:
            return None

class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    amount_inr = serializers.SerializerMethodField()
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'payment_gateway', 'transaction_id', 
            'amount', 'amount_inr', 'currency', 'status', 'gateway_order_id',
            'gateway_payment_id', 'failure_reason', 'created_at', 'updated_at',
            'user_first_name', 'user_last_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_amount_inr(self, obj):
        return obj.amount / 100

    def get_user_first_name(self, obj):
        try:
            return obj.subscription.user.first_name
        except Exception:
            return ''

    def get_user_last_name(self, obj):
        try:
            return obj.subscription.user.last_name
        except Exception:
            return ''

class RazorpayOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazorpayOrder
        fields = ['subscription']
    
    def validate_subscription(self, value):
        # Ensure subscription belongs to the requesting user
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid subscription")
        
        # Ensure subscription is in pending payment status
        if value.status != 'PENDING_PAYMENT':
            raise serializers.ValidationError("Subscription is not pending payment")
        
        return value

class RazorpayOrderSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    amount_inr = serializers.SerializerMethodField()
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RazorpayOrder
        fields = [
            'id', 'order_id', 'amount', 'amount_inr', 'currency', 
            'subscription', 'status', 'receipt', 'created_at',
            'user_first_name', 'user_last_name'
        ]
    
    def get_amount_inr(self, obj):
        return obj.amount / 100

    def get_user_first_name(self, obj):
        try:
            return obj.subscription.user.first_name
        except Exception:
            return ''

    def get_user_last_name(self, obj):
        try:
            return obj.subscription.user.last_name
        except Exception:
            return ''

class PaymentVerificationSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=200)

class RefundRequestSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    original_payment = PaymentSerializer(read_only=True)
    amount_inr = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'subscription', 'original_payment', 'requested_at', 
            'amount', 'amount_inr', 'status', 'admin_comment', 
            'processed_at', 'refund_transaction_id'
        ]
        read_only_fields = [
            'id', 'requested_at', 'processed_at', 'refund_transaction_id'
        ]
    
    def get_amount_inr(self, obj):
        return obj.amount / 100
