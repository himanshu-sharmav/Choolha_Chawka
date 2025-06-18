from django.contrib import admin
from .models import Plan, Subscription, Leave
from django.utils import timezone

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'service_type', 'base_price', 'breakfast_addon_price', 'is_active')
    list_filter = ('service_type', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('service_type', 'base_price')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'subscription_type', 'start_date', 'adjusted_end_date', 
                    'status', 'total_paid')
    list_filter = ('status', 'subscription_type', 'breakfast_included')
    search_fields = ('user__username', 'user__email', 'user__phone')
    readonly_fields = ('created_at', 'updated_at', 'base_price', 'breakfast_addon_price')
    date_hierarchy = 'start_date'

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
