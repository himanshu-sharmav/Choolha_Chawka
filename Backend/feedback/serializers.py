from rest_framework import serializers
from django.utils import timezone
from .models import Feedback, FeedbackAttachment
from accounts.serializers import UserProfileSerializer
from subscriptions.serializers import SubscriptionBasicSerializer

class FeedbackAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackAttachment
        fields = ['id', 'file', 'original_filename', 'file_size', 'uploaded_at']
        read_only_fields = ['id', 'original_filename', 'file_size', 'uploaded_at']

class FeedbackSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    subscription = SubscriptionBasicSerializer(read_only=True)
    responded_by = UserProfileSerializer(read_only=True)
    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)
    days_since_created = serializers.ReadOnlyField()
    is_food_complaint = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'feedback_type', 'subject', 'message', 'rating',
            'subscription', 'meal_date', 'meal_type', 'priority', 'status',
            'created_at', 'updated_at', 'admin_response', 'responded_at',
            'responded_by', 'attachments', 'days_since_created', 
            'is_food_complaint', 'is_urgent'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'responded_at', 
            'responded_by', 'priority'
        ]
    
    def validate(self, data):
        # Validate food complaint specific fields
        if data.get('feedback_type') == 'food_complaint':
            if not data.get('meal_date'):
                raise serializers.ValidationError({
                    'meal_date': 'Meal date is required for food complaints.'
                })
            if not data.get('meal_type'):
                raise serializers.ValidationError({
                    'meal_type': 'Meal type is required for food complaints.'
                })
        
        # Validate meal date is not in future
        if data.get('meal_date') and data['meal_date'] > timezone.now().date():
            raise serializers.ValidationError({
                'meal_date': 'Meal date cannot be in the future.'
            })
        
        return data

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'feedback_type', 'subject', 'message', 'rating',
            'subscription', 'meal_date', 'meal_type'
        ]
    
    def validate(self, data):
        # Same validation as FeedbackSerializer
        if data.get('feedback_type') == 'food_complaint':
            if not data.get('meal_date'):
                raise serializers.ValidationError({
                    'meal_date': 'Meal date is required for food complaints.'
                })
            if not data.get('meal_type'):
                raise serializers.ValidationError({
                    'meal_type': 'Meal type is required for food complaints.'
                })
        
        if data.get('meal_date') and data['meal_date'] > timezone.now().date():
            raise serializers.ValidationError({
                'meal_date': 'Meal date cannot be in the future.'
            })
        
        return data

class FeedbackUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating feedback"""
    class Meta:
        model = Feedback
        fields = [
            'feedback_type', 'subject', 'message', 'rating',
            'meal_date', 'meal_type', 'status'
        ]
    
    def validate(self, data):
        # Same validation as FeedbackSerializer
        if data.get('feedback_type') == 'food_complaint':
            if not data.get('meal_date'):
                raise serializers.ValidationError({
                    'meal_date': 'Meal date is required for food complaints.'
                })
            if not data.get('meal_type'):
                raise serializers.ValidationError({
                    'meal_type': 'Meal type is required for food complaints.'
                })
        
        if data.get('meal_date') and data['meal_date'] > timezone.now().date():
            raise serializers.ValidationError({
                'meal_date': 'Meal date cannot be in the future.'
            })
        
        return data

class FeedbackAdminSerializer(serializers.ModelSerializer):
    """Enhanced serializer for admin/mess_owner with additional fields"""
    user = UserProfileSerializer(read_only=True)
    subscription = SubscriptionBasicSerializer(read_only=True)
    responded_by = UserProfileSerializer(read_only=True)
    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)
    days_since_created = serializers.ReadOnlyField()
    is_food_complaint = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'feedback_type', 'subject', 'message', 'rating',
            'subscription', 'meal_date', 'meal_type', 'priority', 'status',
            'created_at', 'updated_at', 'admin_response', 'responded_at',
            'responded_by', 'attachments', 'days_since_created', 
            'is_food_complaint', 'is_urgent'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'responded_at', 
            'responded_by'
        ]
    
    def validate(self, data):
        # Same validation as FeedbackSerializer
        if data.get('feedback_type') == 'food_complaint':
            if not data.get('meal_date'):
                raise serializers.ValidationError({
                    'meal_date': 'Meal date is required for food complaints.'
                })
            if not data.get('meal_type'):
                raise serializers.ValidationError({
                    'meal_type': 'Meal type is required for food complaints.'
                })
        
        if data.get('meal_date') and data['meal_date'] > timezone.now().date():
            raise serializers.ValidationError({
                'meal_date': 'Meal date cannot be in the future.'
            })
        
        return data

class FeedbackResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['admin_response']
    
    def validate_admin_response(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Response cannot be empty.")
        return value

class FeedbackStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['status']
