from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserRegistrationView, 
    VerifyOTPView, 
    ResendOTPView, 
    UserProfileView,
    CompleteProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', obtain_auth_token, name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
