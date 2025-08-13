from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend   

from django.core.cache import cache
from core.permissions import IsCustomer, IsMessOwner
from .models import Feedback, FeedbackAttachment
from .serializers import (
    FeedbackSerializer, FeedbackCreateSerializer, FeedbackAttachmentSerializer,
    FeedbackResponseSerializer, FeedbackStatusUpdateSerializer
)
from notifications.services import NotificationService

class FeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for customer feedback management"""
    serializer_class = FeedbackSerializer
    permission_classes = [IsCustomer]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['feedback_type', 'status', 'priority']
    search_fields = ['subject', 'message']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Prevent schema generation (drf_yasg) from triggering logic that needs auth
        if getattr(self, 'swagger_fake_view', False):
            return Feedback.objects.none()
    
        if self.request.user.is_authenticated:
            return Feedback.objects.select_related(
                'user', 'subscription', 'subscription__plan', 'responded_by'
            ).prefetch_related('attachments').filter(user=self.request.user)
    
        return Feedback.objects.none()

    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        return FeedbackSerializer
    
    def perform_create(self, serializer):
        # Just save the feedback - NO EMAIL NOTIFICATIONS
        # Dashboard will show new feedback automatically
        feedback = serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to return full feedback object with ID"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save(user=request.user)
        
        # Return full feedback object including ID
        response_serializer = FeedbackSerializer(feedback)
        return Response({
            'success': True,
            'message': 'Feedback created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_attachment(self, request, pk=None):
           """Add attachment to feedback (limited to 2 attachments max)"""
           feedback = self.get_object()

           # ✅ NEW: Check existing attachment count first
           existing_attachments_count = feedback.attachments.count()

           if existing_attachments_count >= 2:
               return Response({
                   'success': False,
                   'error': 'Maximum of 2 attachments allowed per feedback. Please remove an existing attachment to add a new one.'
               }, status=status.HTTP_400_BAD_REQUEST)

           if 'file' not in request.FILES:
               return Response({
                   'error': 'No file provided'
               }, status=status.HTTP_400_BAD_REQUEST)

           file = request.FILES['file']

           # Validate file size (5MB limit)
           if file.size > 5 * 1024 * 1024:
               return Response({
                   'error': 'File size must be less than 5MB'
               }, status=status.HTTP_400_BAD_REQUEST)

           # Validate file type
           allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain']
           if file.content_type not in allowed_types:
               return Response({
                   'error': 'File type not allowed. Only images, PDF, and text files are allowed.'
               }, status=status.HTTP_400_BAD_REQUEST)

           attachment = FeedbackAttachment.objects.create(
               feedback=feedback,
               file=file
           )

           serializer = FeedbackAttachmentSerializer(attachment)
           return Response({
               'success': True,
               'message': f'Attachment added successfully. ({existing_attachments_count + 1}/2 used)',
               'data': serializer.data
           }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_attachment(self, request, pk=None):
        """Remove attachment from feedback"""
        feedback = self.get_object()
        attachment_id = request.data.get('attachment_id')
        
        try:
            attachment = feedback.attachments.get(id=attachment_id)
            attachment.delete()
            return Response({'success': True, 'message': 'Attachment removed'})
        except FeedbackAttachment.DoesNotExist:
            return Response({
                'error': 'Attachment not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Get user's feedback statistics"""
        user_feedbacks = self.get_queryset()
        
        stats = {
            'total_feedbacks': user_feedbacks.count(),
            'food_complaints': user_feedbacks.filter(feedback_type='food_complaint').count(),
            'general_feedbacks': user_feedbacks.filter(feedback_type='general_feedback').count(),
            'resolved_feedbacks': user_feedbacks.filter(status='resolved').count(),
            'pending_feedbacks': user_feedbacks.filter(status__in=['open', 'in_progress']).count(),
            'average_rating': user_feedbacks.filter(rating__isnull=False).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating'] or 0,
        }
        
        return Response(stats)



class AdminFeedbackViewSet(viewsets.ModelViewSet):
    """Optimized ViewSet for admin feedback management with caching"""
    serializer_class = FeedbackSerializer
    permission_classes = [IsMessOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['feedback_type', 'status', 'priority', 'user']
    search_fields = ['subject', 'message', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'priority', 'status', 'responded_at']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        return Feedback.objects.select_related(
            'user', 'subscription', 'subscription__plan', 'responded_by'
        ).prefetch_related('attachments').all()
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to feedback with cache invalidation"""
        feedback = self.get_object()
        serializer = FeedbackResponseSerializer(data=request.data)
        
        if serializer.is_valid():
            feedback.admin_response = serializer.validated_data['admin_response']
            feedback.responded_at = timezone.now()
            feedback.responded_by = request.user
            feedback.status = 'in_progress'
            feedback.save()
            
            # Clear dashboard cache after responding
            # self._clear_dashboard_cache()
            
            return Response({
                'success': True,
                'message': 'Response sent successfully',
                'feedback': FeedbackSerializer(feedback).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update feedback status with cache invalidation"""
        feedback = self.get_object()
        serializer = FeedbackStatusUpdateSerializer(
            feedback, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Clear dashboard cache after status update
            # self._clear_dashboard_cache()
            
            return Response({
                'success': True,
                'message': 'Status updated successfully',
                'feedback': FeedbackSerializer(feedback).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Optimized dashboard statistics with caching"""
        # Check cache first
        cache_key = 'admin_feedback_dashboard_stats'
        stats = cache.get(cache_key)
        if stats:
            return Response(stats)
        
        # Use minimal fields for counting
        base_qs = Feedback.objects.only(
            'id', 'feedback_type', 'status', 'priority', 
            'admin_response', 'responded_at', 'created_at', 'rating'
        )
        
        now = timezone.now()
        today = now.date()
        one_week_ago = now - timezone.timedelta(days=7)
        
        # Single aggregated query instead of multiple counts
        aggregate_data = base_qs.aggregate(
            total_feedbacks=Count('id'),
            food_complaints=Count('id', filter=Q(feedback_type='food_complaint')),
            general_feedbacks=Count('id', filter=Q(feedback_type='general_feedback')),
            open_feedbacks=Count('id', filter=Q(status='open')),
            urgent_feedbacks=Count('id', filter=Q(priority='urgent')),
            high_priority_feedbacks=Count('id', filter=Q(priority='high')),
            resolved_today=Count('id', filter=Q(status='resolved', responded_at__date=today)),
            recent_complaints=Count('id', filter=Q(
                feedback_type='food_complaint', 
                created_at__gte=one_week_ago
            )),
            average_rating=Avg('rating'),
            responded_count=Count('id', filter=~Q(admin_response__in=[None, '']))
        )
        
        # Calculate response rate
        total_count = aggregate_data['total_feedbacks']
        responded_count = aggregate_data['responded_count']
        response_rate = round((responded_count / total_count) * 100, 2) if total_count > 0 else 0
        
        stats = {
            'total_feedbacks': aggregate_data['total_feedbacks'],
            'food_complaints': aggregate_data['food_complaints'],
            'general_feedbacks': aggregate_data['general_feedbacks'],
            'open_feedbacks': aggregate_data['open_feedbacks'],
            'urgent_feedbacks': aggregate_data['urgent_feedbacks'],
            'high_priority_feedbacks': aggregate_data['high_priority_feedbacks'],
            'resolved_today': aggregate_data['resolved_today'],
            'average_rating': aggregate_data['average_rating'] or 0,
            'response_rate': response_rate,
            'recent_complaints': aggregate_data['recent_complaints'],
        }
        
        # Cache for 3 minutes
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def urgent_complaints(self, request):
        """Cached urgent complaints"""
        cache_key = 'urgent_complaints'
        complaints = cache.get(cache_key)
        
        if not complaints:
            urgent_complaints = self.get_queryset().filter(
                feedback_type='food_complaint',
                priority__in=['urgent', 'high'],
                status__in=['open', 'in_progress']
            )[:10]  # Limit results
            
            serializer = self.get_serializer(urgent_complaints, many=True)
            complaints = serializer.data
        
        return Response(complaints)
    
    @action(detail=False, methods=['get'])
    def pending_responses(self, request):
        """Get feedbacks pending admin response - cached"""
        cache_key = 'pending_responses'
        pending = cache.get(cache_key)
        
        if not pending:
            pending_qs = self.get_queryset().filter(
                Q(admin_response__isnull=True) | Q(admin_response=''),
                status__in=['open', 'in_progress']
            )[:20]  # Limit results
            
            serializer = self.get_serializer(pending_qs, many=True)
            pending = serializer.data
        
        return Response(pending)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent feedback activity for dashboard - cached"""
        cache_key = 'recent_activity'
        recent = cache.get(cache_key)
        
        if not recent:
            recent_qs = self.get_queryset().filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            )[:10]
            
            serializer = self.get_serializer(recent_qs, many=True)
            recent = serializer.data
        
        return Response(recent)
    
    @action(detail=False, methods=['get'])
    def priority_summary(self, request):
        """Optimized priority summary with single query"""
        cache_key = 'feedback_priority_summary'
        summary = cache.get(cache_key)
        
        if not summary:
            # Single query to get all priority counts
            priority_data = Feedback.objects.aggregate(
                **{f'{priority}_count': Count('id', filter=Q(priority=priority))
                   for priority, _ in Feedback.PRIORITY_LEVELS},
                **{f'{priority}_open': Count('id', filter=Q(priority=priority, status='open'))
                   for priority, _ in Feedback.PRIORITY_LEVELS}
            )
            
            summary = {}
            for priority, label in Feedback.PRIORITY_LEVELS:
                summary[priority] = {
                    'label': label,
                    'count': priority_data.get(f'{priority}_count', 0),
                    'open_count': priority_data.get(f'{priority}_open', 0)
                }
            
        return Response(summary)
    
  
