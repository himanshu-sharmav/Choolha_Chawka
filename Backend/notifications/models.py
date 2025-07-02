from django.db import models
from django.conf import settings

class NotificationLog(models.Model):
    """Log sent notifications for tracking purposes"""
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    notification_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['status', 'sent_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.username} via {self.channel}"
