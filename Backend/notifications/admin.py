from django.contrib import admin
from .models import NotificationTemplate, NotificationLog

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'is_active', 'created_at')
    list_filter = ('channel', 'is_active')
    search_fields = ('name', 'subject')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'channel', 'is_active')
        }),
        ('Email Template', {
            'fields': ('subject', 'email_template'),
            'classes': ('collapse',)
        }),
        ('SMS Template', {
            'fields': ('sms_template',),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'channel', 'status', 'sent_at')
    list_filter = ('notification_type', 'channel', 'status', 'sent_at')
    search_fields = ('user__username', 'user__email', 'subject')
    readonly_fields = ('sent_at',)
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
