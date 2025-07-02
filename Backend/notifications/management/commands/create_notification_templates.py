from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate

class Command(BaseCommand):
    help = 'Create default notification templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'welcome',
                'channel': 'email',
                'subject': 'Welcome to {{ platform_name }}!',
                'email_template': '''
Dear {{ user_name }},

Welcome to {{ platform_name }}! We're excited to have you on board.

Your account has been successfully created. You can now:
- Browse our meal plans
- Subscribe to mess or tiffin services
- Manage your subscriptions

Login to your account: {{ login_url }}

If you have any questions, feel free to contact us at {{ support_email }}.

Best regards,
{{ platform_name }} Team
                ''',
                'sms_template': 'Welcome to {{ platform_name }}! Your account is ready. Login at {{ login_url }}'
            },
            {
                'name': 'profile_complete',
                'channel': 'email',
                'subject': 'Profile Setup Complete - {{ platform_name }}',
                'email_template': '''
Hi {{ user_name }},

Great! Your profile setup is now complete.

You can now:
- Subscribe to meal plans
- Request leaves
- Manage your account

Visit your dashboard: {{ dashboard_url }}

Best regards,
{{ platform_name }} Team
                ''',
            },
            {
                'name': 'subscription_created',
                'channel': 'email',
                'subject': 'Complete Your Payment - {{ plan_name }}',
                'email_template': '''
Hi {{ user_name }},

Your subscription for {{ plan_name }} has been created!

Plan: {{ plan_name }}
Amount: ₹{{ amount }}

Please complete your payment to activate your subscription.
Pay now: {{ payment_url }}

Best regards,
{{ platform_name }} Team
                ''',
            },
            {
                'name': 'payment_success',
                'channel': 'both',
                'subject': 'Payment Successful - {{ plan_name }}',
                'email_template': '''
Hi {{ user_name }},

Your payment has been successfully processed!

Plan: {{ plan_name }}
Amount Paid: ₹{{ amount }}
Subscription Period: {{ start_date }} to {{ end_date }}

Your subscription is now active. Enjoy your meals!

Best regards,
{{ platform_name }} Team
                ''',
                'sms_template': 'Payment successful! Your {{ plan_name }} subscription is now active from {{ start_date }} to {{ end_date }}. Enjoy your meals!'
            },
            {
                'name': 'leave_submitted',
                'channel': 'email',
                'subject': 'Leave Request Submitted',
                'email_template': '''
Hi {{ user_name }},

Your leave request has been submitted successfully.

Leave Period: {{ start_date }} to {{ end_date }} ({{ leave_days }} days)
Status: Pending Approval

You will be notified once your leave is reviewed.

Best regards,
{{ platform_name }} Team
                ''',
            },
            {
                'name': 'leave_approved',
                'channel': 'both',
                'subject': 'Leave Request Approved',
                'email_template': '''
Hi {{ user_name }},

Good news! Your leave request has been approved.

Leave Period: {{ start_date }} to {{ end_date }} ({{ leave_days }} days)
{% if admin_comment %}Admin Comment: {{ admin_comment }}{% endif %}

Your subscription has been extended accordingly.

Best regards,
{{ platform_name }} Team
                ''',
                'sms_template': 'Your leave request for {{ start_date }} to {{ end_date }} has been approved. Subscription extended accordingly.'
            },
            {
                'name': 'leave_rejected',
                'channel': 'both',
                'subject': 'Leave Request Rejected',
                'email_template': '''
Hi {{ user_name }},

We regret to inform you that your leave request has been rejected.

Leave Period: {{ start_date }} to {{ end_date }} ({{ leave_days }} days)
{% if admin_comment %}Reason: {{ admin_comment }}{% endif %}

Please contact us if you have any questions.

Best regards,
{{ platform_name }} Team
                ''',
                'sms_template': 'Your leave request for {{ start_date }} to {{ end_date }} has been rejected. {% if admin_comment %}Reason: {{ admin_comment }}{% endif %}'
            },
            {
    'name': 'subscription_cancelled',
    'channel': 'email',
    'subject': 'Subscription Cancelled - {{ plan_name }}',
    'email_template': '''
Dear {{ user_name }},

Your subscription has been cancelled successfully.

Subscription Details:
- Plan: {{ plan_name }}
- Cancelled Date: {{ cancelled_date }}
{% if refund_amount > 0 %}
- Refund Amount: ₹{{ refund_amount }}
- Refund Status: {{ refund_status }}

Your refund will be processed within 5-7 business days.
{% else %}
- No refund applicable for this cancellation.
{% endif %}

We're sorry to see you go! If you have any feedback or faced any issues, please reach out to us at {{ support_email }}.

You can always resubscribe anytime in the future.

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Your {{ plan_name }} subscription has been cancelled. {% if refund_amount > 0 %}Refund of ₹{{ refund_amount }} will be processed soon.{% endif %}'
},

{
    'name': 'payment_failed',
    'channel': 'both',
    'subject': 'Payment Failed - {{ plan_name }}',
    'email_template': '''
Hi {{ user_name }},

We were unable to process your payment for {{ plan_name }}.

Amount: ₹{{ amount }}

Please try again or contact us if the issue persists.
Retry Payment: {{ retry_payment_url }}

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Payment failed for {{ plan_name }}. Please retry at {{ retry_payment_url }} or contact support.'
},
{
    'name': 'subscription_expiring',
    'channel': 'both',
    'subject': 'Subscription Expiring Soon - {{ plan_name }}',
    'email_template': '''
Hi {{ user_name }},

Your subscription for {{ plan_name }} is expiring soon.

Expiry Date: {{ expiry_date }}

Renew now to continue enjoying our services.
Renew Subscription: {{ renew_url }}

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Your {{ plan_name }} subscription expires on {{ expiry_date }}. Renew at {{ renew_url }}'
},
{
    'name': 'refund_processed',
    'channel': 'both',
    'subject': 'Refund Approved - ₹{{ refund_amount }}',
    'email_template': '''
Dear {{ user_name }},

Good news! Your refund request has been approved.

Refund Details:
- Plan: {{ plan_name }}
- Refund Amount: ₹{{ refund_amount }}
- Approved Date: {{ processed_date }}

Your refund will be processed manually and credited within 5-7 business days.

If you have any questions, please contact us.

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Your refund of ₹{{ refund_amount }} for {{ plan_name }} has been approved. Amount will be credited in 5-7 days.'
},

{
    'name': 'refund_rejected',
    'channel': 'email',
    'subject': 'Refund Request Rejected',
    'email_template': '''
Dear {{ user_name }},

We regret to inform you that your refund request has been rejected.

Request Details:
- Plan: {{ plan_name }}
- Requested Amount: ₹{{ refund_amount }}
{% if admin_comment %}- Reason: {{ admin_comment }}{% endif %}

If you believe this is an error or have questions, please contact us at {{ support_email }}.

Best regards,
{{ platform_name }} Team
    ''',
},
# Add these templates to your existing list

{
    'name': 'password_reset',
    'channel': 'email',
    'subject': 'Reset Your Password - {{ platform_name }}',
    'email_template': '''
Dear {{ user_name }},

You requested to reset your password for your {{ platform_name }} account.

Click the link below to reset your password:
{{ reset_url }}

This link will expire in 24 hours for security reasons.

If you didn't request this password reset, please ignore this email or contact us at {{ support_email }}.

Best regards,
{{ platform_name }} Team
    ''',
},
{
    'name': 'password_changed',
    'channel': 'email',
    'subject': 'Password Changed Successfully - {{ platform_name }}',
    'email_template': '''
Dear {{ user_name }},

Your password has been changed successfully.

If you made this change, no further action is required.

If you didn't change your password, please contact us immediately at {{ support_email }}.

Login to your account: {{ login_url }}

Best regards,
{{ platform_name }} Team
    ''',
},
{
    'name': 'payment_reminder',
    'channel': 'both',
    'subject': 'Payment Reminder - {{ plan_name }}',
    'email_template': '''
Dear {{ user_name }},

This is a friendly reminder that your payment for {{ plan_name }} is still pending.

Subscription Details:
- Plan: {{ plan_name }}
- Amount: ₹{{ amount }}
- Days Pending: {{ days_pending }}

Complete your payment now to activate your subscription:
{{ payment_url }}

If you have any questions, please contact us.

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Payment reminder: Your {{ plan_name }} subscription (₹{{ amount }}) is pending for {{ days_pending }} days. Pay now: {{ payment_url }}'
},

{
    'name': 'subscription_expired',
    'channel': 'both',
    'subject': 'Subscription Expired - {{ plan_name }}',
    'email_template': '''
Dear {{ user_name }},

Your subscription for {{ plan_name }} has expired.

Expired Date: {{ expired_date }}

You can resubscribe anytime to continue enjoying our services:
{{ renew_url }}

We hope to serve you again soon!

Best regards,
{{ platform_name }} Team
    ''',
    'sms_template': 'Your {{ plan_name }} subscription expired on {{ expired_date }}. Resubscribe at {{ renew_url }}'
},
{
    'name': 'subscription_renewed',
    'channel': 'email',
    'subject': 'Subscription Renewed - {{ plan_name }}',
    'email_template': '''
Dear {{ user_name }},

Great! Your subscription has been renewed successfully.

New Subscription Details:
- Plan: {{ plan_name }}
- Start Date: {{ start_date }}
- End Date: {{ end_date }}
- Amount: ₹{{ amount }}

Thank you for continuing with us!

Best regards,
{{ platform_name }} Team
    ''',
},

            {
                'name': 'new_user_joined',
                'channel': 'email',
                'subject': 'New User Subscription - {{ new_user_name }}',
                'email_template': '''
Hello,

A new user has subscribed to your mess service.

User: {{ new_user_name }}
Phone: {{ new_user_phone }}
Plan: {{ plan_name }}
Start Date: {{ start_date }}

View details: {{ dashboard_url }}

Best regards,
{{ platform_name }} Team
                ''',
            },
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.get_name_display()}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new templates')
        )
