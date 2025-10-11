#!/usr/bin/env python
"""
Test email connection from Railway environment using Resend API
Run this on your Railway Celery worker to test email connectivity
"""

import os
import sys
import django
import resend
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_email_connection():
    """Test if we can send emails from Railway using Resend API"""
    try:
        print("🔧 Testing Resend API configuration...")
        print(f"RESEND_API_KEY: {'Set' if settings.RESEND_API_KEY else 'Not set'}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        print("\n📧 Attempting to send test email via Resend API...")
        
        # Configure Resend
        resend.api_key = settings.RESEND_API_KEY
        
        # Send a test email via Resend API
        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": ["your-test-email@example.com"],  # Replace with your email
            "subject": "Test Email from Railway via Resend API",
            "html": "<h1>Test Email</h1><p>This is a test email to verify Resend API connectivity from Railway Celery worker.</p>",
            "text": "Test Email\n\nThis is a test email to verify Resend API connectivity from Railway Celery worker.",
        }
        
        result = resend.Emails.send(params)
        
        print(f"✅ Email sent successfully via Resend API! ID: {result.get('id')}")
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
