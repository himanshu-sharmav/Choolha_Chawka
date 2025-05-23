from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, RegularProfile, OTPVerificationAttempt, OTPThrottle

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False

class RegularProfileInline(admin.StackedInline):
    model = RegularProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'user_type', 'status', 'phone_verified')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('status', 'user_type', 'phone_verified')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('phone', 'user_type', 'status', 'phone_verified')}),
        ('Preferences', {'fields': ('is_tiffin_user', 'is_mess_user', 'preferred_delivery_time')}),
    )
    
    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        if obj.user_type == 'student':
            return [StudentProfileInline]
        elif obj.user_type == 'regular':
            return [RegularProfileInline]
        return []

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile)
admin.site.register(RegularProfile)
admin.site.register(OTPVerificationAttempt)
admin.site.register(OTPThrottle)
