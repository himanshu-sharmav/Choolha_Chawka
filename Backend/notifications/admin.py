from django.contrib import admin
from django.utils.html import format_html
from .models import NotificationLog

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'channel', 'status_badge', 
        'recipient_email', 'sent_at'
    ]
    list_filter = ['notification_type', 'channel', 'status', 'sent_at']
    search_fields = ['user__username', 'user__email', 'subject', 'recipient_email']
    readonly_fields = ['sent_at']
    
    def status_badge(self, obj):
        colors = {
            'sent': 'green',
            'failed': 'red',
            'pending': 'orange'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
