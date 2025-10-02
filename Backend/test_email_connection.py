#!/usr/bin/env python
"""
Test email connection from Railway environment
Run this on your Railway Celery worker to test email connectivity
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_email_connection():
    """Test if we can send emails from Railway"""
    try:
        print("🔧 Testing email configuration...")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        print("\n📧 Attempting to send test email...")
        
        # Send a test email
        result = send_mail(
            subject='Test Email from Railway',
            message='This is a test email to verify connectivity from Railway Celery worker.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['your-test-email@example.com'],  # Replace with your email
            fail_silently=False,
        )
        
        print(f"✅ Email sent successfully! Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 Starting email connection test...")
    success = test_email_connection()
    if success:
        print("✅ Email connection test PASSED")
    else:
        print("❌ Email connection test FAILED")
    sys.exit(0 if success else 1)
