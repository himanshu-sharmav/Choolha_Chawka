from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

def _get_user(pk):
    return User.objects.get(id=pk)

# Authentication and Profile Tasks
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def async_send_welcome_email(self, user_id):
    logger.info(f"🚀 [async_send_welcome_email] Starting for user_id: {user_id}")
    try:
        # Add database connection retry logic
        from django.db import connection
        connection.ensure_connection()
        
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'platform_name': 'Choolha Chowka',
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@choolhachowka.com'),
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login",
        }

        subject = render_to_string('notifications/subjects/welcome.txt', context).strip()
        html_message = render_to_string('notifications/email/welcome.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        result = msg.send()
        
        logger.info(f"✅ [async_send_welcome_email] Email sent to {user.email}, result: {result}")
        return f"Welcome email sent to {user.email}"
        
    except Exception as e:
        logger.error(f"❌ [async_send_welcome_email] Failed for user_id {user_id}: {str(e)}")
        return f"Welcome email failed: {str(e)}"
    logger.info(f"🚀 [async_send_welcome_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'platform_name': 'Choolha Chowka',
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@choolhachowka.com'),
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login",
        }

        subject = render_to_string('notifications/subjects/welcome.txt', context).strip()
        html_message = render_to_string('notifications/email/welcome.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        result = msg.send()
        
        logger.info(f"✅ [async_send_welcome_email] Email sent to {user.email}, result: {result}")
        return f"Welcome email sent to {user.email}"
        
    except Exception as e:
        logger.error(f"❌ [async_send_welcome_email] Failed for user_id {user_id}: {str(e)}")
        return f"Welcome email failed: {str(e)}"

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def async_send_profile_complete_email(self, user_id):
    logger.info(f"🚀 [async_send_profile_complete_email] Starting for user_id: {user_id}")
    try:
        # Add database connection retry logic
        from django.db import connection
        connection.ensure_connection()
        
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
        }
        
        subject = render_to_string('notifications/subjects/profile_complete.txt', context).strip()
        html_message = render_to_string('notifications/email/profile_complete.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_profile_complete_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_profile_complete_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_profile_complete_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
        }
        
        subject = render_to_string('notifications/subjects/profile_complete.txt', context).strip()
        html_message = render_to_string('notifications/email/profile_complete.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_profile_complete_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_profile_complete_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_password_changed_email(user_id):
    logger.info(f"🚀 [async_send_password_changed_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login",
        }
        
        subject = render_to_string('notifications/subjects/password_changed.txt', context).strip()
        html_message = render_to_string('notifications/email/password_changed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_password_changed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_password_changed_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_password_changed_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login",
        }
        
        subject = render_to_string('notifications/subjects/password_changed.txt', context).strip()
        html_message = render_to_string('notifications/email/password_changed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_password_changed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_password_changed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_password_reset_email(user_id, uidb64, token):
    logger.info(f"🚀 [async_send_password_reset_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'reset_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password/{uidb64}/{token}/",
        }
        
        subject = render_to_string('notifications/subjects/password_reset.txt', context).strip()
        html_message = render_to_string('notifications/email/password_reset.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_password_reset_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_password_reset_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_password_reset_email] Starting for user_id: {user_id}")
    try:
        user = _get_user(user_id)
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'reset_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password/{uidb64}/{token}/",
        }
        
        subject = render_to_string('notifications/subjects/password_reset.txt', context).strip()
        html_message = render_to_string('notifications/email/password_reset.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_password_reset_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_password_reset_email] Failed for user_id {user_id}: {str(e)}")

# Subscription Tasks
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def async_send_subscription_created_email(self, user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_created_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        # Add database connection retry logic
        from django.db import connection
        connection.ensure_connection()
        
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': subscription.total_paid,
            'payment_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/payment/{subscription.id}",
        }
        
        subject = render_to_string('notifications/subjects/subscription_created.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_created.html', context)
        text_message = strip_tags(html_message)

        # Use Resend API instead of SMTP for better reliability
        try:
            from notifications.resend_api import send_email_via_resend_api
            success, result = send_email_via_resend_api(
                to_email=user.email,
                subject=subject,
                html_content=html_message,
                text_content=text_message
            )
            if success:
                logger.info(f"✅ [async_send_subscription_created_email] Email sent via Resend API to {user.email}")
            else:
                logger.error(f"❌ [async_send_subscription_created_email] Resend API failed for {user.email}: {result}")
                # Fallback to SMTP
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@choolhachowka.com'),
                    to=[user.email]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()
                logger.info(f"✅ [async_send_subscription_created_email] Email sent via SMTP fallback to {user.email}")
        except Exception as email_error:
            logger.error(f"❌ [async_send_subscription_created_email] Email sending failed for {user.email}: {str(email_error)}")
            # Try SMTP fallback
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@choolhachowka.com'),
                    to=[user.email]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()
                logger.info(f"✅ [async_send_subscription_created_email] Email sent via SMTP fallback to {user.email}")
            except Exception as smtp_error:
                logger.error(f"❌ [async_send_subscription_created_email] Both Resend API and SMTP failed for {user.email}: {str(smtp_error)}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_created_email] Failed for user_id {user_id}: {str(e)}")

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def async_send_subscription_cancelled_email(self, user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_cancelled_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        # Add database connection retry logic
        from django.db import connection
        connection.ensure_connection()
        
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'cancelled_date': subscription.cancelled_at.strftime('%B %d, %Y') if subscription.cancelled_at else 'Today',
            'refund_amount': subscription.refund_amount_calculated / 100 if subscription.refund_amount_calculated else 0,
            'refund_status': subscription.get_refund_status_display() if subscription.refund_status else 'No refund',
        }
        
        subject = render_to_string('notifications/subjects/subscription_cancelled.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_cancelled.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_cancelled_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_cancelled_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_subscription_renewed_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_renewed_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'new_subscription': subscription,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
            'amount': subscription.total_paid,
        }
        
        subject = render_to_string('notifications/subjects/subscription_renewed.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_renewed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_renewed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_renewed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_subscription_expiring_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_expiring_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expiry_date': subscription.adjusted_end_date,
            'renew_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/renew/{subscription.id}",
        }
        
        subject = render_to_string('notifications/subjects/subscription_expiring.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_expiring.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_expiring_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_expiring_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_subscription_cancelled_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'cancelled_date': subscription.cancelled_at.strftime('%B %d, %Y') if subscription.cancelled_at else 'Today',
            'refund_amount': subscription.refund_amount_calculated / 100 if subscription.refund_amount_calculated else 0,
            'refund_status': subscription.get_refund_status_display() if subscription.refund_status else 'No refund',
        }
        
        subject = render_to_string('notifications/subjects/subscription_cancelled.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_cancelled.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_cancelled_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_cancelled_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_subscription_renewed_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_renewed_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'new_subscription': subscription,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
            'amount': subscription.total_paid,
        }
        
        subject = render_to_string('notifications/subjects/subscription_renewed.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_renewed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_renewed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_renewed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_subscription_expiring_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_expiring_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expiry_date': subscription.adjusted_end_date,
            'renew_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/renew/{subscription.id}",
        }
        
        subject = render_to_string('notifications/subjects/subscription_expiring.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_expiring.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_expiring_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_expiring_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_subscription_expired_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_expired_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expired_date': subscription.adjusted_end_date,
            'renew_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/plans",
        }
        
        subject = render_to_string('notifications/subjects/subscription_expired.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_expired.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_expired_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_expired_email] Failed for user_id {user_id}: {str(e)}")
def async_send_subscription_expired_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_subscription_expired_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expired_date': subscription.adjusted_end_date,
            'renew_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/plans",
        }
        
        subject = render_to_string('notifications/subjects/subscription_expired.txt', context).strip()
        html_message = render_to_string('notifications/email/subscription_expired.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_subscription_expired_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_subscription_expired_email] Failed for user_id {user_id}: {str(e)}")

# Leave Management Tasks
@shared_task
def async_send_leave_submitted_email(user_id, leave_id):
    logger.info(f"🚀 [async_send_leave_submitted_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
        }
        
        subject = render_to_string('notifications/subjects/leave_submitted.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_submitted.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_submitted_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_submitted_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_leave_submitted_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
        }
        
        subject = render_to_string('notifications/subjects/leave_submitted.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_submitted.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_submitted_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_submitted_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_leave_approved_email(user_id, leave_id):
    logger.info(f"🚀 [async_send_leave_approved_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/leave_approved.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_approved.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_approved_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_approved_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_leave_approved_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/leave_approved.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_approved.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_approved_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_approved_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_leave_rejected_email(user_id, leave_id):
    logger.info(f"🚀 [async_send_leave_rejected_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/leave_rejected.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_rejected.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_rejected_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_rejected_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_leave_rejected_email] Starting for user_id: {user_id}, leave_id: {leave_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Leave
        leave = Leave.objects.get(id=leave_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/leave_rejected.txt', context).strip()
        html_message = render_to_string('notifications/email/leave_rejected.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_leave_rejected_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_leave_rejected_email] Failed for user_id {user_id}: {str(e)}")

# Payment Tasks
@shared_task
def async_send_payment_success_email(user_id, subscription_id, payment_id):
    logger.info(f"🚀 [async_send_payment_success_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}, payment_id: {payment_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from payments.models import Payment
        subscription = Subscription.objects.get(id=subscription_id)
        payment = Payment.objects.get(id=payment_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'payment': payment,
            'plan_name': subscription.plan.name,
            'amount': payment.amount / 100,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
        }
        
        subject = render_to_string('notifications/subjects/payment_success.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_success.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_success_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_success_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_payment_success_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}, payment_id: {payment_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from payments.models import Payment
        subscription = Subscription.objects.get(id=subscription_id)
        payment = Payment.objects.get(id=payment_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'payment': payment,
            'plan_name': subscription.plan.name,
            'amount': payment.amount / 100,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
        }
        
        subject = render_to_string('notifications/subjects/payment_success.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_success.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_success_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_success_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_payment_failed_email(user_id, subscription_id, order_id):
    logger.info(f"🚀 [async_send_payment_failed_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}, order_id: {order_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from payments.models import PaymentOrder
        subscription = Subscription.objects.get(id=subscription_id)
        order = PaymentOrder.objects.get(id=order_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': order.amount / 100,
            'retry_payment_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/payment/{subscription.id}",
        }
        
        subject = render_to_string('notifications/subjects/payment_failed.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_failed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_failed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_failed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_payment_reminder_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_payment_reminder_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from django.utils import timezone
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': subscription.total_paid,
            'payment_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/payment/{subscription.id}",
            'days_pending': (timezone.now().date() - subscription.created_at.date()).days,
        }
        
        subject = render_to_string('notifications/subjects/payment_reminder.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_reminder.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_reminder_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_reminder_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_payment_failed_email(user_id, subscription_id, order_id):
    logger.info(f"🚀 [async_send_payment_failed_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}, order_id: {order_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from payments.models import PaymentOrder
        subscription = Subscription.objects.get(id=subscription_id)
        order = PaymentOrder.objects.get(id=order_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': order.amount / 100,
            'retry_payment_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/payment/{subscription.id}",
        }
        
        subject = render_to_string('notifications/subjects/payment_failed.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_failed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_failed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_failed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_payment_reminder_email(user_id, subscription_id):
    logger.info(f"🚀 [async_send_payment_reminder_email] Starting for user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        from django.utils import timezone
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': subscription.total_paid,
            'payment_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/payment/{subscription.id}",
            'days_pending': (timezone.now().date() - subscription.created_at.date()).days,
        }
        
        subject = render_to_string('notifications/subjects/payment_reminder.txt', context).strip()
        html_message = render_to_string('notifications/email/payment_reminder.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_payment_reminder_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_payment_reminder_email] Failed for user_id {user_id}: {str(e)}")

# Refund Tasks
@shared_task
def async_send_refund_processed_email(user_id, refund_id):
    logger.info(f"🚀 [async_send_refund_processed_email] Starting for user_id: {user_id}, refund_id: {refund_id}")
    try:
        user = _get_user(user_id)
        from payments.models import RefundRequest
        refund_request = RefundRequest.objects.get(id=refund_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount,
            'processed_date': refund_request.processed_at.strftime('%B %d, %Y') if refund_request.processed_at else 'Today',
            'refund_id': refund_request.id,
            'admin_comment': refund_request.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/refund_processed.txt', context).strip()
        html_message = render_to_string('notifications/email/refund_processed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_refund_processed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_refund_processed_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_refund_processed_email] Starting for user_id: {user_id}, refund_id: {refund_id}")
    try:
        user = _get_user(user_id)
        from payments.models import RefundRequest
        refund_request = RefundRequest.objects.get(id=refund_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount,
            'processed_date': refund_request.processed_at.strftime('%B %d, %Y') if refund_request.processed_at else 'Today',
            'refund_id': refund_request.id,
            'admin_comment': refund_request.admin_comment,
        }
        
        subject = render_to_string('notifications/subjects/refund_processed.txt', context).strip()
        html_message = render_to_string('notifications/email/refund_processed.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_refund_processed_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_refund_processed_email] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_refund_rejected_email(user_id, refund_id):
    logger.info(f"🚀 [async_send_refund_rejected_email] Starting for user_id: {user_id}, refund_id: {refund_id}")
    try:
        user = _get_user(user_id)
        from payments.models import RefundRequest
        refund_request = RefundRequest.objects.get(id=refund_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount,
            'admin_comment': refund_request.admin_comment,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@choolhachowka.com'),
        }
        
        subject = render_to_string('notifications/subjects/refund_rejected.txt', context).strip()
        html_message = render_to_string('notifications/email/refund_rejected.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_refund_rejected_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_refund_rejected_email] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_refund_rejected_email] Starting for user_id: {user_id}, refund_id: {refund_id}")
    try:
        user = _get_user(user_id)
        from payments.models import RefundRequest
        refund_request = RefundRequest.objects.get(id=refund_id)
        
        context = {
            'user': user,
            'user_name': user.get_full_name() or user.username,
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount,
            'admin_comment': refund_request.admin_comment,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@choolhachowka.com'),
        }
        
        subject = render_to_string('notifications/subjects/refund_rejected.txt', context).strip()
        html_message = render_to_string('notifications/email/refund_rejected.html', context)
        text_message = strip_tags(html_message)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        logger.info(f"✅ [async_send_refund_rejected_email] Email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_refund_rejected_email] Failed for user_id {user_id}: {str(e)}")

# Mess Owner Notification Tasks
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def async_send_new_user_joined_email(self, mess_owner_ids, user_id, subscription_id):
    logger.info(f"🚀 [async_send_new_user_joined_email] Starting for mess_owner_ids: {mess_owner_ids}, user_id: {user_id}, subscription_id: {subscription_id}")
    try:
        # Add database connection retry logic
        from django.db import connection
        connection.ensure_connection()
        
        user = _get_user(user_id)
        from subscriptions.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        mess_owners = User.objects.filter(id__in=mess_owner_ids)
        
        context = {
            'new_user_name': user.get_full_name() or user.username,
            'new_user_phone': user.phone,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date,
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/owner/users",
        }
        
        subject = render_to_string('notifications/subjects/new_user_joined.txt', context).strip()
        html_message = render_to_string('notifications/email/new_user_joined.html', context)
        text_message = strip_tags(html_message)

        for owner in mess_owners:
            owner_context = context.copy()
            owner_context.update({
                'user': owner,
                'user_name': owner.get_full_name() or owner.username,
            })
            
            # Use Resend API instead of SMTP for better reliability
            try:
                from notifications.resend_api import send_email_via_resend_api
                success, result = send_email_via_resend_api(
                    to_email=owner.email,
                    subject=subject,
                    html_content=html_message,
                    text_content=text_message
                )
                if success:
                    logger.info(f"✅ [async_send_new_user_joined_email] Email sent via Resend API to mess owner {owner.email}")
                else:
                    logger.error(f"❌ [async_send_new_user_joined_email] Resend API failed for {owner.email}: {result}")
                    # Fallback to SMTP
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@choolhachowka.com'),
                        to=[owner.email]
                    )
                    msg.attach_alternative(html_message, "text/html")
                    msg.send()
                    logger.info(f"✅ [async_send_new_user_joined_email] Email sent via SMTP fallback to mess owner {owner.email}")
            except Exception as email_error:
                logger.error(f"❌ [async_send_new_user_joined_email] Email sending failed for {owner.email}: {str(email_error)}")
                # Try SMTP fallback
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@choolhachowka.com'),
                        to=[owner.email]
                    )
                    msg.attach_alternative(html_message, "text/html")
                    msg.send()
                    logger.info(f"✅ [async_send_new_user_joined_email] Email sent via SMTP fallback to mess owner {owner.email}")
                except Exception as smtp_error:
                    logger.error(f"❌ [async_send_new_user_joined_email] Both Resend API and SMTP failed for {owner.email}: {str(smtp_error)}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_new_user_joined_email] Failed for mess_owner_ids {mess_owner_ids}: {str(e)}")

# SMS Tasks
@shared_task
def async_send_otp_sms(user_id, otp):
    logger.info(f"🚀 [async_send_otp_sms] Starting for user_id: {user_id}, otp: {otp}")
    try:
        user = _get_user(user_id)
        from core.sms import send_sms
        context = {'otp': otp}
        
        message = render_to_string('notifications/sms/otp_verification.txt', context).strip()
        result = send_sms(user.phone, message)
        
        logger.info(f"✅ [async_send_otp_sms] SMS sent to {user.phone}: {result}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_otp_sms] Failed for user_id {user_id}: {str(e)}")
    logger.info(f"🚀 [async_send_otp_sms] Starting for user_id: {user_id}, otp: {otp}")
    try:
        user = _get_user(user_id)
        from core.sms import send_sms
        context = {'otp': otp}
        
        message = render_to_string('notifications/sms/otp_verification.txt', context).strip()
        result = send_sms(user.phone, message)
        
        logger.info(f"✅ [async_send_otp_sms] SMS sent to {user.phone}: {result}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_otp_sms] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_password_reset_otp_sms(user_id, otp):
    logger.info(f"🚀 [async_send_password_reset_otp_sms] Starting for user_id: {user_id}, otp: {otp}")
    try:
        user = _get_user(user_id)
        from core.sms import send_sms
        context = {'otp': otp}
        
        message = render_to_string('notifications/sms/password_reset_otp.txt', context).strip()
        result = send_sms(user.phone, message)
        
        logger.info(f"✅ [async_send_password_reset_otp_sms] SMS sent to {user.phone}: {result}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_password_reset_otp_sms] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_login_verification_sms(user_id, code):
    logger.info(f"🚀 [async_send_login_verification_sms] Starting for user_id: {user_id}, code: {code}")
    try:
        user = _get_user(user_id)
        from core.sms import send_sms
        context = {'verification_code': code}
        
        message = render_to_string('notifications/sms/login_verification.txt', context).strip()
        result = send_sms(user.phone, message)
        
        logger.info(f"✅ [async_send_login_verification_sms] SMS sent to {user.phone}: {result}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_login_verification_sms] Failed for user_id {user_id}: {str(e)}")

@shared_task
def async_send_security_alert_sms(user_id, alert_message):
    logger.info(f"🚀 [async_send_security_alert_sms] Starting for user_id: {user_id}, alert: {alert_message}")
    try:
        user = _get_user(user_id)
        from core.sms import send_sms
        context = {'alert_message': alert_message}
        
        message = render_to_string('notifications/sms/security_alert.txt', context).strip()
        result = send_sms(user.phone, message)
        
        logger.info(f"✅ [async_send_security_alert_sms] SMS sent to {user.phone}: {result}")
        
    except Exception as e:
        logger.error(f"❌ [async_send_security_alert_sms] Failed for user_id {user_id}: {str(e)}")