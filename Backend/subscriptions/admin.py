from django.contrib import admin
from .models import Plan, Subscription, Leave, Cart, CartItem, BundleOrder
from django.utils import timezone


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'service_type', 'base_price', 'duration_days', 
                    'min_duration_days', 'max_duration_days', 'allow_custom_duration', 'is_active')
    list_filter = ('service_type', 'is_active', 'allow_custom_duration')
    search_fields = ('name', 'code')
    ordering = ('service_type', 'base_price')
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'service_type', 'included_meals')
        }),
        ('Pricing', {
            'fields': ('base_price', 'duration_days', 'daily_rate_override')
        }),
        ('Custom Duration Settings', {
            'fields': ('allow_custom_duration', 'min_duration_days', 'max_duration_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'adjusted_end_date', 
                    'status', 'total_paid', 'bundle_order')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email', 'user__phone')
    readonly_fields = ('created_at', 'updated_at', 'base_price')
    date_hierarchy = 'start_date'
    raw_id_fields = ('user', 'plan', 'bundle_order')


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'leave_start_date', 'leave_end_date', 
                    'duration_days', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('subscription__user__username',)
    readonly_fields = ('requested_at', 'duration_days')
    date_hierarchy = 'leave_start_date'
    
    actions = ['approve_leaves', 'reject_leaves']
    
    def approve_leaves(self, request, queryset):
        for leave in queryset.filter(status='PENDING'):
            leave.status = 'AUTO_APPROVED'
            leave.approved_at = timezone.now()
            leave.save()
        self.message_user(request, f'{queryset.count()} leaves approved')
    
    def reject_leaves(self, request, queryset):
        for leave in queryset.filter(status='PENDING'):
            leave.status = 'REJECTED'
            leave.rejected_at = timezone.now()
            leave.save()
        self.message_user(request, f'{queryset.count()} leaves rejected')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('calculated_price',)
    
    def calculated_price(self, obj):
        return f"₹{obj.calculated_price}"
    calculated_price.short_description = 'Price'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_item_count', 'get_total', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def get_item_count(self, obj):
        return obj.get_item_count()
    get_item_count.short_description = 'Items'
    
    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'plan', 'custom_duration_days', 'calculated_price_display', 'created_at')
    list_filter = ('plan',)
    search_fields = ('cart__user__username', 'plan__name')
    
    def calculated_price_display(self, obj):
        return f"₹{obj.calculated_price}"
    calculated_price_display.short_description = 'Price'


class BundleOrderSubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    readonly_fields = ('plan', 'total_paid', 'start_date', 'adjusted_end_date', 'status')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BundleOrder)
class BundleOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'get_subscription_count', 
                    'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('created_at', 'paid_at', 'razorpay_order_id', 'razorpay_payment_id')
    date_hierarchy = 'created_at'
    inlines = [BundleOrderSubscriptionInline]
    
    def get_subscription_count(self, obj):
        return obj.get_subscription_count()
    get_subscription_count.short_description = 'Subscriptions'
