from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
# from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserRegistrationView, 
    VerifyOTPView, 
    ResendOTPView, 
    UserProfileView,
    CompleteProfileView,
    UpdateProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    LogoutView,
    OwnerUserViewSet
)

router = DefaultRouter()
router.register(r'owner/users', OwnerUserViewSet, basename='owner-users')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    # path('login/', obtain_auth_token, name='login'),
     path('login/', TokenObtainPairView.as_view(), name='login'),  # JWT login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # JWT refresh
    path('logout/', LogoutView.as_view(), name='logout'),  # JWT logout
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
     path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
] + router.urls
