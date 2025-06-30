from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Feedback, FeedbackAttachment

class FeedbackAttachmentInline(admin.TabularInline):
    model = FeedbackAttachment
    extra = 0
    readonly_fields = ['original_filename', 'file_size', 'uploaded_at']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'user', 'feedback_type', 'priority_badge', 
        'status_badge', 'rating', 'created_at', 'has_response'
    ]
    list_filter = [
        'feedback_type', 'priority', 'status', 'created_at', 
        'meal_type', 'responded_at'
    ]
    search_fields = [
        'subject', 'message', 'user__username', 'user__email',
        'admin_response'
    ]
    readonly_fields = ['created_at', 'updated_at', 'days_since_created']
    inlines = [FeedbackAttachmentInline]
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('user', 'feedback_type', 'subject', 'message', 'rating')
        }),
        ('Context', {
            'fields': ('subscription', 'meal_date', 'meal_type'),
            'classes': ('collapse',)
        }),
        ('Management', {
            'fields': ('priority', 'status', 'created_at', 'updated_at', 'days_since_created')
        }),
        ('Admin Response', {
            'fields': ('admin_response', 'responded_by', 'responded_at')
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'set_high_priority']
    
    def priority_badge(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'urgent': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'open': 'red',
            'in_progress': 'orange',
            'resolved': 'green',
            'closed': 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_response(self, obj):
        return bool(obj.admin_response)
    has_response.boolean = True
    has_response.short_description = 'Responded'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
        self.message_user(request, f'{queryset.count()} feedbacks marked as resolved')
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, f'{queryset.count()} feedbacks marked as in progress')
    
    def set_high_priority(self, request, queryset):
        queryset.update(priority='high')
        self.message_user(request, f'{queryset.count()} feedbacks set to high priority')

@admin.register(FeedbackAttachment)
class FeedbackAttachmentAdmin(admin.ModelAdmin):
    list_display = ['feedback', 'original_filename', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['feedback__subject', 'original_filename']
    readonly_fields = ['original_filename', 'file_size', 'uploaded_at']
