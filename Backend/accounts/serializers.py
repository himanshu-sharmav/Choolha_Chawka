from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import StudentProfile, RegularProfile

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'confirm_password')
    
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
        fields = ('institute', 'student_id', 'hostel')

class RegularProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularProfile
        fields = ('address', 'landmark')

class UserProfileSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=False, required=False)
    regular_profile = RegularProfileSerializer(read_only=False, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'user_type', 
                  'is_tiffin_user', 'is_mess_user', 'preferred_delivery_time', 
                  'status', 'student_profile', 'regular_profile')
        read_only_fields = ('id', 'username', 'email', 'phone', 'status')
