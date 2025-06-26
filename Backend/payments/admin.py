from django.contrib import admin
from django.utils import timezone
from .models import Payment, RazorpayOrder, RefundRequest

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'subscription', 'amount_inr', 'status', 
        'payment_gateway', 'created_at'
    )
    list_filter = ('status', 'payment_gateway', 'created_at')
    search_fields = (
        'user__username', 'user__email', 'transaction_id', 
        'gateway_payment_id'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def amount_inr(self, obj):
        return f"₹{obj.amount / 100}"
    amount_inr.short_description = 'Amount (INR)'

@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'user', 'subscription', 'amount_inr', 
        'status', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'user__username', 'payment_id')
    readonly_fields = ('created_at', 'updated_at')
    
    def amount_inr(self, obj):
        return f"₹{obj.amount / 100}"
    amount_inr.short_description = 'Amount (INR)'

@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = (
        'subscription', 'requested_by', 'amount_inr', 
        'status', 'requested_at'
    )
    list_filter = ('status', 'requested_at')
    search_fields = ('subscription__user__username', 'refund_transaction_id')
    readonly_fields = ('requested_at',)
    actions = ['approve_refunds', 'reject_refunds']
    
    def amount_inr(self, obj):
        return f"₹{obj.amount / 100}"
    amount_inr.short_description = 'Amount (INR)'
    
    def approve_refunds(self, request, queryset):
        queryset.filter(status='PENDING').update(
            status='APPROVED', 
            processed_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} refunds approved')
    
    def reject_refunds(self, request, queryset):
        queryset.filter(status='PENDING').update(
            status='REJECTED',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} refunds rejected')
