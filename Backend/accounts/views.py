from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    StudentProfileSerializer, 
    RegularProfileSerializer,
    MessOwnerProfileSerializer
)
from notifications.services import send_welcome_email, send_profile_complete_email
from .models import OTPThrottle, OTPVerificationAttempt, StudentProfile, RegularProfile,MessOwnerProfile
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from notifications.services import send_password_reset_email, send_password_changed_email
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)

User = get_user_model()

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if phone is already registered
            phone = serializer.validated_data.get('phone')
            if User.objects.filter(phone=phone).exists():
                return Response({
                    'success': False,
                    'message': 'Phone number already registered'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Check if we can send OTP to this phone
            if not OTPThrottle.can_send_otp(phone):
                return Response({
                    'success': False,
                    'message': 'Too many verification attempts. Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
            # Create user with unverified status
            user = serializer.save()
            
            # Generate and send OTP
            otp, sent = user.generate_and_send_otp()
            
            if sent:
                return Response({
                    'success': True,
                    'message': 'Registration successful. Please verify your phone number with the OTP sent.',
                    'user_id': user.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'User created but failed to send OTP. Please request a new OTP.'
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        
        try:
            user = User.objects.get(phone=phone)
            
            # Check for too many attempts
            if not OTPVerificationAttempt.check_attempts(user):
                return Response({
                    'success': False,
                    'message': 'Too many failed attempts. Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Record this attempt
            attempt = OTPVerificationAttempt(user=user)
            
            # Verify OTP
            is_valid, message = user.verify_otp(otp)
            attempt.successful = is_valid
            attempt.save()
            
            if is_valid:
                # Create auth token
                token, created = Token.objects.get_or_create(user=user)
                
                 # Send welcome email for first-time phone verification
                if user.status in ['registration_complete', 'profile_complete']:
                    try:
                        send_welcome_email(user)
                    except Exception as e:
                        # Log error but don't fail the verification
                        print(f"Failed to send welcome email: {e}")

                return Response({
                    'success': True,
                    'message': message,
                    'token': token.key,
                    'user': UserProfileSerializer(user).data
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid phone number'
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        
        try:
            user = User.objects.get(phone=phone)
            
            # Check if already verified
            if user.phone_verified:
                return Response({
                    'success': False,
                    'message': 'Phone already verified. Please login.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check throttling
            if not OTPThrottle.can_send_otp(phone):
                return Response({
                    'success': False,
                    'message': 'Too many verification attempts. Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate and send new OTP
            otp, sent = user.generate_and_send_otp()
            
            if sent:
                return Response({
                    'success': True,
                    'message': 'OTP sent successfully'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send OTP. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid phone number'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        data = request.data
        
         # Track if profile was completed in this request
        was_profile_incomplete = user.status != 'profile_complete'
        # Update user type
        user.user_type = data.get('user_type', user.user_type)
        
        # Handle mess owner profile
        if user.user_type == 'mess_owner':
            mess_owner_data = data.get('mess_owner_profile', {})
            if not mess_owner_data:
                return Response({
                    'success': False,
                    'message': 'Mess owner profile data required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update mess owner profile
            mess_owner_profile, created = MessOwnerProfile.objects.get_or_create(user=user)
            mess_owner_profile.mess_name = mess_owner_data.get('mess_name', '')
            mess_owner_profile.business_address = mess_owner_data.get('business_address', '')
            mess_owner_profile.business_phone = mess_owner_data.get('business_phone', '')
            mess_owner_profile.business_email = mess_owner_data.get('business_email', '')
            mess_owner_profile.gst_number = mess_owner_data.get('gst_number', '')
            mess_owner_profile.save()
            
            # Clean up any customer profiles
            StudentProfile.objects.filter(user=user).delete()
            RegularProfile.objects.filter(user=user).delete()
            
            # Auto-complete profile for mess owners
            user.complete_profile()
            
        elif user.user_type in ['student', 'regular']:
            # Handle customer types (existing logic)
            user.is_tiffin_user = data.get('is_tiffin_user', user.is_tiffin_user)
            user.is_mess_user = data.get('is_mess_user', user.is_mess_user)
            user.preferred_delivery_time = data.get('preferred_delivery_time', user.preferred_delivery_time)
            
            if user.user_type == 'student':
                student_data = data.get('student_profile', {})
                if not student_data:
                    return Response({
                        'success': False,
                        'message': 'Student profile data required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                student_profile, created = StudentProfile.objects.get_or_create(user=user)
                student_profile.institute = student_data.get('institute', '')
                student_profile.student_id = student_data.get('student_id', '')
                student_profile.hostel = student_data.get('hostel', '')
                student_profile.save()
                
                # Clean up other profiles
                RegularProfile.objects.filter(user=user).delete()
                MessOwnerProfile.objects.filter(user=user).delete()
                
            elif user.user_type == 'regular':
                regular_data = data.get('regular_profile', {})
                if not regular_data:
                    return Response({
                        'success': False,
                        'message': 'Regular profile data required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                regular_profile, created = RegularProfile.objects.get_or_create(user=user)
                regular_profile.address = regular_data.get('address', '')
                regular_profile.landmark = regular_data.get('landmark', '')
                regular_profile.save()
                
                # Clean up other profiles
                StudentProfile.objects.filter(user=user).delete()
                MessOwnerProfile.objects.filter(user=user).delete()
            
            # Check profile completion for customers
            profile_complete = False
            if user.user_type == 'student':
                profile_complete = (
                    hasattr(user, 'student_profile') and 
                    bool(user.student_profile.institute) and 
                    bool(user.student_profile.hostel)
                )
            elif user.user_type == 'regular':
                profile_complete = (
                    hasattr(user, 'regular_profile') and 
                    bool(user.regular_profile.address)
                )
                
            if (profile_complete and 
                (user.is_tiffin_user or user.is_mess_user) and 
                user.status == 'registration_complete'):
                user.complete_profile()
        else:
            return Response({
                'success': False,
                'message': 'Invalid user type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.save()

        # Send profile complete email if profile was just completed
        if was_profile_incomplete and user.status == 'profile_complete':
            try:
                send_profile_complete_email(user)
            except Exception as e:
                # Log error but don't fail the profile completion
                print(f"Failed to send profile complete email: {e}")
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': UserProfileSerializer(user).data
        })


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Send password reset email
        try:
            send_password_reset_email(user, uidb64, token)
            return Response({
                'success': True,
                'message': 'Password reset email sent successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to send password reset email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Send confirmation email
        try:
            send_password_changed_email(user)
        except Exception as e:
            print(f"Failed to send password changed email: {e}")
        
        return Response({
            'success': True,
            'message': 'Password reset successfully'
        })

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Send confirmation email
        try:
            send_password_changed_email(user)
        except Exception as e:
            print(f"Failed to send password changed email: {e}")
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })
