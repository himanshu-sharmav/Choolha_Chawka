from django.core.management.base import BaseCommand
from django.conf import settings
import resend


class Command(BaseCommand):
    help = 'Test Resend API email sending'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            required=True
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        try:
            self.stdout.write("🔧 Testing Resend API configuration...")
            self.stdout.write(f"RESEND_API_KEY: {'Set' if settings.RESEND_API_KEY else 'Not set'}")
            self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            self.stdout.write(f"\n📧 Sending test email to {test_email}...")
            
            # Configure Resend
            resend.api_key = settings.RESEND_API_KEY
            
            # Send test email
            params = {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [test_email],
                "subject": "Test Email from Railway via Resend API",
                "html": """
                <h1>🎉 Test Email Successful!</h1>
                <p>This is a test email sent from your Railway Celery worker using the Resend API.</p>
                <p>If you received this email, your email configuration is working correctly!</p>
                <hr>
                <p><small>Sent from Choolha Chowka notification system</small></p>
                """,
                "text": "Test Email Successful!\n\nThis is a test email sent from your Railway Celery worker using the Resend API.\n\nIf you received this email, your email configuration is working correctly!\n\nSent from Choolha Chowka notification system",
            }
            
            result = resend.Emails.send(params)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Email sent successfully! ID: {result.get("id")}')
            )
            self.stdout.write("Check your email inbox and Resend dashboard for confirmation.")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Email failed: {str(e)}')
            )
            import traceback
            self.stdout.write("Full traceback:")
            self.stdout.write(traceback.format_exc())
