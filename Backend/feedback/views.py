from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend   

from core.permissions import IsCustomer, IsMessOwner
from .models import Feedback, FeedbackAttachment
from .serializers import (
    FeedbackSerializer, FeedbackCreateSerializer, FeedbackAttachmentSerializer,
    FeedbackResponseSerializer, FeedbackStatusUpdateSerializer,
    FeedbackUpdateSerializer, FeedbackAdminSerializer
)
from notifications.services import NotificationService

class FeedbackViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for customer feedback management"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['feedback_type', 'status', 'priority']
    search_fields = ['subject', 'message']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Prevent schema generation (drf_yasg) from triggering logic that needs auth
        if getattr(self, 'swagger_fake_view', False):
            return Feedback.objects.none()
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None) if user.is_authenticated else None
        
        if user_type == 'mess_owner':
            return Feedback.objects.select_related(
                'user', 'subscription', 'subscription__plan', 'responded_by'
            ).prefetch_related('attachments').all()
        elif user.is_authenticated:
            return Feedback.objects.select_related(
                'subscription', 'subscription__plan', 'responded_by'
            ).prefetch_related('attachments').filter(user=user)
        else:
            return Feedback.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FeedbackUpdateSerializer
        else:
            user_type = getattr(self.request.user, 'user_type', None) if self.request.user.is_authenticated else None
            if user_type == 'mess_owner':
                return FeedbackAdminSerializer
            return FeedbackSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new feedback"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the user to the current user
        feedback = serializer.save(user=request.user)
        
        return Response({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.id,
            'data': FeedbackSerializer(feedback).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update feedback (full update)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        # Only mess_owner can update feedback or users can update their own pending feedback
        if user_type != 'mess_owner' and (instance.user != request.user or instance.status != 'open'):
            return Response({
                'success': False,
                'message': 'You can only update your own pending feedback'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Feedback updated successfully',
            'data': FeedbackSerializer(feedback).data
        })

    def partial_update(self, request, *args, **kwargs):
        """Partial update feedback"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete feedback"""
        instance = self.get_object()
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        # Only mess_owner can delete feedback or users can delete their own pending feedback
        if user_type != 'mess_owner' and (instance.user != request.user or instance.status != 'open'):
            return Response({
                'success': False,
                'message': 'You can only delete your own pending feedback'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        return Response({
            'success': True,
            'message': 'Feedback deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_attachment(self, request, pk=None):
        """Add attachment to feedback"""
        feedback = self.get_object()
        
        # Only allow attachment to own feedback or if mess_owner
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        if user_type != 'mess_owner' and feedback.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only add attachments to your own feedback'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Validate file size (5MB limit)
        if file.size > 5 * 1024 * 1024:
            return Response({
                'success': False,
                'message': 'File size must be less than 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain']
        if file.content_type not in allowed_types:
            return Response({
                'success': False,
                'message': 'File type not allowed. Only images, PDF, and text files are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attachment = FeedbackAttachment.objects.create(
            feedback=feedback,
            file=file
        )
        
        return Response({
            'success': True,
            'message': 'Attachment added successfully',
            'data': FeedbackAttachmentSerializer(attachment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_attachment(self, request, pk=None):
        """Remove attachment from feedback"""
        feedback = self.get_object()
        attachment_id = request.data.get('attachment_id')
        
        # Only allow removal from own feedback or if mess_owner
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        if user_type != 'mess_owner' and feedback.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only remove attachments from your own feedback'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not attachment_id:
            return Response({
                'success': False,
                'message': 'Attachment ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            attachment = feedback.attachments.get(id=attachment_id)
            attachment.delete()
            return Response({
                'success': True, 
                'message': 'Attachment removed successfully'
            })
        except FeedbackAttachment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Attachment not found'
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

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to feedback (mess_owner only)"""
        user_type = getattr(request.user, 'user_type', None) if request.user.is_authenticated else None
        
        if user_type != 'mess_owner':
            return Response({
                'success': False,
                'message': 'Only mess owners can respond to feedback'
            }, status=status.HTTP_403_FORBIDDEN)
        
        feedback = self.get_object()
        response_message = request.data.get('admin_response')
        
        if not response_message:
            return Response({
                'success': False,
                'message': 'Response message is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        feedback.admin_response = response_message
        feedback.status = 'in_progress'
        feedback.responded_by = request.user
        feedback.responded_at = timezone.now()
        feedback.save()
        
        return Response({
            'success': True,
            'message': 'Response added successfully',
            'data': FeedbackSerializer(feedback).data
        })

class AdminFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for admin feedback management with enhanced features"""
    serializer_class = FeedbackAdminSerializer
    permission_classes = [IsMessOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['feedback_type', 'status', 'priority', 'user']
    search_fields = ['subject', 'message', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'priority', 'status', 'responded_at']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Feedback.objects.none()
            
        return Feedback.objects.select_related(
            'user', 'subscription', 'subscription__plan', 'responded_by'
        ).prefetch_related('attachments').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FeedbackUpdateSerializer
        return FeedbackAdminSerializer

    def create(self, request, *args, **kwargs):
        """Create feedback on behalf of user (admin only)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Feedback created successfully',
            'feedback_id': feedback.id,
            'data': FeedbackAdminSerializer(feedback).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update any feedback (admin only)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Feedback updated successfully',
            'data': FeedbackAdminSerializer(feedback).data
        })

    def destroy(self, request, *args, **kwargs):
        """Delete any feedback (admin only)"""
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Feedback deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to feedback"""
        feedback = self.get_object()
        serializer = FeedbackResponseSerializer(data=request.data)
        
        if serializer.is_valid():
            feedback.admin_response = serializer.validated_data['admin_response']
            feedback.responded_at = timezone.now()
            feedback.responded_by = request.user
            feedback.status = 'in_progress'
            feedback.save()
            
            return Response({
                'success': True,
                'message': 'Response sent successfully',
                'feedback': FeedbackAdminSerializer(feedback).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update feedback status"""
        feedback = self.get_object()
        serializer = FeedbackStatusUpdateSerializer(
            feedback, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Status updated successfully',
                'feedback': FeedbackAdminSerializer(feedback).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark feedback as resolved"""
        feedback = self.get_object()
        feedback.status = 'resolved'
        feedback.save()
        
        return Response({
            'success': True,
            'message': 'Feedback marked as resolved',
            'status': feedback.status
        })

    @action(detail=True, methods=['post'])
    def mark_urgent(self, request, pk=None):
        """Mark feedback as urgent priority"""
        feedback = self.get_object()
        feedback.priority = 'urgent'
        feedback.save()
        
        return Response({
            'success': True,
            'message': 'Feedback marked as urgent',
            'priority': feedback.priority
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for admin"""
        all_feedbacks = self.get_queryset()
        
        stats = {
            'total_feedbacks': all_feedbacks.count(),
            'food_complaints': all_feedbacks.filter(feedback_type='food_complaint').count(),
            'general_feedbacks': all_feedbacks.filter(feedback_type='general_feedback').count(),
            'open_feedbacks': all_feedbacks.filter(status='open').count(),
            'urgent_feedbacks': all_feedbacks.filter(priority='urgent').count(),
            'high_priority_feedbacks': all_feedbacks.filter(priority='high').count(),
            'resolved_today': all_feedbacks.filter(
                status='resolved',
                responded_at__date=timezone.now().date()
            ).count(),
            'average_rating': all_feedbacks.filter(rating__isnull=False).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating'] or 0,
            'response_rate': self._calculate_response_rate(all_feedbacks),
            'recent_complaints': all_feedbacks.filter(
                feedback_type='food_complaint',
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        return Response(stats)
    
    def _calculate_response_rate(self, feedbacks):
        """Calculate response rate percentage"""
        total = feedbacks.count()
        if total == 0:
            return 0
        
        responded = feedbacks.filter(
            admin_response__isnull=False
        ).exclude(admin_response='').count()
        
        return round((responded / total) * 100, 2)
    
    @action(detail=False, methods=['get'])
    def urgent_complaints(self, request):
        """Get urgent food complaints"""
        urgent_complaints = self.get_queryset().filter(
            feedback_type='food_complaint',
            priority__in=['urgent', 'high'],
            status__in=['open', 'in_progress']
        )
        
        serializer = self.get_serializer(urgent_complaints, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_responses(self, request):
        """Get feedbacks pending admin response"""
        pending = self.get_queryset().filter(
            Q(admin_response__isnull=True) | Q(admin_response=''),
            status__in=['open', 'in_progress']
        )
        
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent feedback activity for dashboard"""
        recent = self.get_queryset().filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )[:10]
        
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def priority_summary(self, request):
        """Get priority-wise feedback summary"""
        summary = {}
        for priority, label in Feedback.PRIORITY_LEVELS:
            summary[priority] = {
                'label': label,
                'count': self.get_queryset().filter(priority=priority).count(),
                'open_count': self.get_queryset().filter(
                    priority=priority, 
                    status='open'
                ).count()
            }
        
        return Response(summary)
