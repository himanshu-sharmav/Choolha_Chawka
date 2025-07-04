from django.db import models
from django.conf import settings

class NotificationTemplate(models.Model):
    """Email/SMS templates for different events"""
    NOTIFICATION_TYPES = [
        ('welcome', 'Welcome Email'),
        ('profile_complete', 'Profile Completed'),
        ('subscription_created', 'Subscription Created'),
        ('payment_success', 'Payment Successful'),
        ('subscription_active', 'Subscription Activated'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('subscription_expiring', 'Subscription Expiring'),
        ('leave_submitted', 'Leave Request Submitted'),
        ('leave_approved', 'Leave Approved'),
        ('leave_rejected', 'Leave Rejected'),
        ('payment_failed', 'Payment Failed'),
        ('refund_processed', 'Refund Processed'),
        ('new_user_joined', 'New User Joined (Owner)'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both'),
    ]
    
    name = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, unique=True)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    subject = models.CharField(max_length=200, blank=True)  # For email
    email_template = models.TextField(blank=True)
    sms_template = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.get_channel_display()}"

class NotificationLog(models.Model):
    """Track all sent notifications"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=10)
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.status}"
