from rest_framework import serializers
from .models import NotificationLog

class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_type', 'channel', 'recipient_email',
            'recipient_phone', 'subject', 'status', 'error_message', 'sent_at'
        ]
        read_only_fields = ['id', 'sent_at']
