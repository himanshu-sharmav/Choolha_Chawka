from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import NotificationLog
from .serializers import NotificationLogSerializer

class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notification history"""
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'channel', 'status']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        return NotificationLog.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics for user"""
        logs = self.get_queryset()
        
        stats = {
            'total_notifications': logs.count(),
            'email_notifications': logs.filter(channel='email').count(),
            'sms_notifications': logs.filter(channel='sms').count(),
            'successful_notifications': logs.filter(status='sent').count(),
            'failed_notifications': logs.filter(status='failed').count(),
            'recent_notifications': logs.filter(
                sent_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get notifications grouped by type"""
        type_stats = logs.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(type_stats)
