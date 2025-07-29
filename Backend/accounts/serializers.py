from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import StudentProfile, RegularProfile, MessOwnerProfile
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.exceptions import ValidationError
from subscriptions.serializers import SubscriptionSerializer

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone','user_type', 'first_name', 'last_name', 'password', 'confirm_password')
    
    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Passwords don't match")
        return data
        
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ('institute', 'student_id', 'hostel','year','course')

class RegularProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularProfile
        fields = ('address', 'landmark')

class MessOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessOwnerProfile
        fields = ('mess_name', 'business_address', 'business_phone', 'business_email', 'gst_number')

class UserProfileSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=False, required=False)
    regular_profile = RegularProfileSerializer(read_only=False, required=False)
    mess_owner_profile = MessOwnerProfileSerializer(read_only=False, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'user_type', 'first_name','last_name',
                  'is_tiffin_user', 'is_mess_user', 'preferred_delivery_time', 
                  'status', 'student_profile', 'regular_profile', 'mess_owner_profile')
        read_only_fields = ('id', 'username', 'email', 'phone', 'status')



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        try:
            uid = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, data['token']):
                raise serializers.ValidationError("Invalid or expired token")
                
            data['user'] = user
            return data
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid token")

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user list"""
    subscription_status = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'phone', 'user_type', 'is_active', 'phone_verified',
            'status', 'last_login', 'subscription_status', 'current_plan'
        ]
    
    def get_subscription_status(self, obj):
        active_subscription = obj.subscriptions.filter(status='ACTIVE').first()
        return active_subscription.status if active_subscription else 'No subscription'
    
    def get_current_plan(self, obj):
        active_subscription = obj.subscriptions.filter(status='ACTIVE').first()
        return active_subscription.plan.name if active_subscription else None

class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual user view"""
    subscriptions = SubscriptionSerializer(many=True, read_only=True)
    profile_info = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'phone', 'user_type', 'is_active', 'phone_verified',
            'status', 'last_login', 'subscriptions',
            'profile_info'
        ]
    
    def get_profile_info(self, obj):
        """Get user-type specific profile information"""
        if obj.user_type == 'student' and hasattr(obj, 'student_profile'):
            return {
                'institute': obj.student_profile.institute,
                'student_id': obj.student_profile.student_id,
                'hostel': obj.student_profile.hostel,
                'year': obj.student_profile.year,
                'course': obj.student_profile.course,
            }
        elif obj.user_type == 'regular' and hasattr(obj, 'regular_profile'):
            return {
                'address': obj.regular_profile.address,
                'landmark': obj.regular_profile.landmark,
            }
        return None
