from rest_framework import serializers
from .models import Payment, RazorpayOrder, RefundRequest
from subscriptions.serializers import SubscriptionSerializer

class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    amount_inr = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'payment_gateway', 'transaction_id', 
            'amount', 'amount_inr', 'currency', 'status', 'gateway_order_id',
            'gateway_payment_id', 'failure_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_amount_inr(self, obj):
        return obj.amount / 100

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
    
    class Meta:
        model = RazorpayOrder
        fields = [
            'id', 'order_id', 'amount', 'amount_inr', 'currency', 
            'subscription', 'status', 'receipt', 'created_at'
        ]
    
    def get_amount_inr(self, obj):
        return obj.amount / 100

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
