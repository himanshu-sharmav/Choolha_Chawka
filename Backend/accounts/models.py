from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('regular', 'Regular Customer'),
        ('mess_owner', 'Mess Owner'),  # Added this
    ]
    STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('registration_complete', 'Registration Complete'),
        ('profile_complete', 'Profile Complete'),
    ]
    
    # Core fields for all users
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, blank=True)
    phone = models.CharField(max_length=15, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='unverified')
    
    # Phone Verification
    phone_verified = models.BooleanField(default=False)
    phone_verification_otp = models.CharField(max_length=6, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    
    # Preference Fields (not used for mess_owner)
    is_tiffin_user = models.BooleanField(default=False)
    is_mess_user = models.BooleanField(default=False)
    preferred_delivery_time = models.CharField(max_length=100, blank=True)
    
    def generate_otp(self):
        """Generate a new OTP and set expiry time"""
        otp = ''.join(random.choices('0123456789', k=6))
        self.phone_verification_otp = otp
        self.otp_expiry = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=['phone_verification_otp', 'otp_expiry'])
        return otp
    
    def verify_otp(self, otp):
        """Verify the OTP and mark phone as verified if correct"""
        if timezone.now() > self.otp_expiry:
            return False, "OTP has expired"
        
        if self.phone_verification_otp != otp:
            return False, "Invalid OTP"
        
        self.phone_verified = True
        self.phone_verification_otp = ''
        # Auto-complete status for mess owners
        if self.user_type == 'mess_owner':
            self.status = 'profile_complete'
        else:
            self.status = 'registration_complete'
        self.save(update_fields=['phone_verified', 'phone_verification_otp', 'status'])
        return True, "Phone verified successfully"
    
    def generate_and_send_otp(self):
        """Generate an OTP, save it, and send via SMS"""
        from core.sms import send_otp
        otp = self.generate_otp()
        
        # Send OTP via SMS
        response = send_otp(self.phone, otp)
        return otp, response['success']
    
    def complete_profile(self):
        """Mark user profile as complete"""
        self.status = 'profile_complete'
        self.save(update_fields=['status'])
    
    def __str__(self):
        return f"{self.username} ({self.phone})"

    class Meta:
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['status']),
            models.Index(fields=['date_joined']),
        ]

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    institute = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50, blank=True)
    hostel = models.CharField(max_length=100)
    year = models.CharField(max_length=10, blank=True)  # New field for year
    course = models.CharField(max_length=100, blank=True)  # New field for course
    
    def __str__(self):
        return f"Student: {self.user.username}"

class RegularProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='regular_profile')
    address = models.TextField()
    landmark = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Regular: {self.user.username}"

class MessOwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mess_owner_profile')
    mess_name = models.CharField(max_length=100)
    business_address = models.TextField()
    business_phone = models.CharField(max_length=15, blank=True)
    business_email = models.EmailField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"Mess Owner: {self.user.username} - {self.mess_name}"

class OTPVerificationAttempt(models.Model):
    """Track verification attempts to prevent brute force"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    
    @classmethod
    def check_attempts(cls, user):
        """Check if too many failed attempts in last hour"""
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        attempts = cls.objects.filter(
            user=user,
            attempt_time__gte=one_hour_ago,
            successful=False
        ).count()
        return attempts < 5  # Allow 5 attempts per hour
    
    def __str__(self):
        return f"{self.user.username} - {self.attempt_time} - {'Success' if self.successful else 'Failed'}"

class OTPThrottle(models.Model):
    """Track OTP sends per phone to prevent abuse"""
    phone = models.CharField(max_length=15, unique=True)
    last_sent = models.DateTimeField(auto_now=True)
    send_count = models.PositiveIntegerField(default=0)
    
    @classmethod
    def can_send_otp(cls, phone):
        """Check if we can send a new OTP to this phone"""
        try:
            record = cls.objects.get(phone=phone)
            # Allow 3 OTPs per hour
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            if record.last_sent > one_hour_ago:
                if record.send_count >= 3:
                    return False
                record.send_count += 1
            else:
                # Reset counter if more than an hour has passed
                record.send_count = 1
            record.save()
            return True
        except cls.DoesNotExist:
            # First time sending OTP to this phone
            cls.objects.create(phone=phone, send_count=1)
            return True
