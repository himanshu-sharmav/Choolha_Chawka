import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from core.sms import send_sms  
from .models import NotificationLog

logger = logging.getLogger(__name__)

# Fix circular import - check for Celery availability without importing tasks
try:
    from celery import current_app
    # Check if Celery is properly configured
    if hasattr(current_app, 'conf') and current_app.conf.broker_url:
        _ASYNC = getattr(settings, 'NOTIFICATIONS_ASYNC', True)
        logger.info(f"✅ Celery detected - ASYNC mode enabled: {_ASYNC}")
    else:
        _ASYNC = False
        logger.warning("❌ Celery not configured - SYNC mode enabled")
except Exception as e:
    _ASYNC = False
    logger.warning(f"❌ Celery not available - SYNC mode enabled. Error: {str(e)}")

class NotificationService:
    
    @staticmethod
    def send_notification(user, template_name, context_data=None, recipient_email=None, recipient_phone=None, channel='email'):
        """
        Send notification using HTML-only email templates
        """
        logger.info(f"🔥 NotificationService called: {template_name} for {user.email}")
        logger.info(f"🎯 Channel: {channel}, _ASYNC: {_ASYNC}")
        
        try:
            # Debug email configuration first
            logger.info("🔧 EMAIL CONFIGURATION:")
            logger.info(f"📧 EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
            logger.info(f"🔌 EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
            logger.info(f"👤 EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')[:10]}...")
            logger.info(f"📨 DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
            logger.info(f"🔒 EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
            
            context_data = context_data or {}
            context_data.update({
                'user': user,
                'user_name': user.get_full_name() or user.username,
                'platform_name': 'Choolha Chowka',
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@choolhaChowka.com'),
                'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            })
            
            # Determine recipients
            email = recipient_email or user.email
            phone = recipient_phone or user.phone
            
            success = True
            error_message = ""
            
            # Send Email (HTML-only)
            if channel in ['email', 'both'] and email:
                logger.info(f"📧 Attempting to send email to {email}")
                try:
                    logger.info(f"📝 Rendering templates for {template_name}")
                    
                    # Render subject and HTML template
                    subject = render_to_string(
                        f'notifications/subjects/{template_name}.txt', 
                        context_data
                    ).strip()
                    logger.info(f"📋 Subject rendered: {subject}")
                    
                    html_message = render_to_string(
                        f'notifications/email/{template_name}.html', 
                        context_data
                    )
                    logger.info(f"🎨 HTML template rendered successfully, length: {len(html_message)}")
                    
                    # Auto-generate plain text from HTML
                    text_message = strip_tags(html_message)
                    logger.info(f"📄 Plain text version generated, length: {len(text_message)}")
                    
                    # Use EmailMultiAlternatives for better email support
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@choolhachowka.com')
                    logger.info(f"📤 Creating email message from {from_email} to {email}")
                    
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_message,  # Fallback plain text
                        from_email=from_email,
                        to=[email]
                    )
                    msg.attach_alternative(html_message, "text/html")
                    logger.info("📨 Email message created successfully")
                    
                    logger.info("🚀 Sending email...")
                    result = msg.send()
                    logger.info(f"✅ Email sent successfully! Result: {result}")
                    
                    # Log successful email
                    NotificationLog.objects.create(
                        user=user,
                        notification_type=template_name,
                        channel='email',
                        recipient_email=email,
                        subject=subject,
                        status='sent'
                    )
                    logger.info("📊 NotificationLog created for successful email")
                    
                except Exception as e:
                    logger.error(f"❌ Email failed: {str(e)}")
                    logger.error(f"📍 Email error traceback:")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    error_message += f"Email failed: {str(e)}; "
                    success = False
                    
                    # Log failed email
                    try:
                        NotificationLog.objects.create(
                            user=user,
                            notification_type=template_name,
                            channel='email',
                            recipient_email=email,
                            status='failed',
                            error_message=str(e)
                        )
                        logger.info("📊 NotificationLog created for failed email")
                    except Exception as log_error:
                        logger.error(f"❌ Failed to create NotificationLog: {log_error}")
            
            # Send SMS (Auth only)
            if channel in ['sms', 'both'] and phone:
                logger.info(f"📱 Attempting to send SMS to {phone}")
                try:
                    sms_message = render_to_string(
                        f'notifications/sms/{template_name}.txt', 
                        context_data
                    ).strip()
                    logger.info(f"💬 SMS message rendered: {sms_message}")
                    
                    sms_response = send_sms(phone, sms_message)
                    logger.info(f"📲 SMS response: {sms_response}")
                    
                    if sms_response.get('success'):
                        status = 'sent'
                        logger.info("✅ SMS sent successfully")
                    else:
                        status = 'failed'
                        error_message += f"SMS failed: {sms_response.get('error', 'Unknown error')}; "
                        success = False
                        logger.error(f"❌ SMS failed: {sms_response.get('error', 'Unknown error')}")
                    
                    # Log SMS notification
                    NotificationLog.objects.create(
                        user=user,
                        notification_type=template_name,
                        channel='sms',
                        recipient_phone=phone,
                        status=status,
                        error_message=sms_response.get('error', '') if not sms_response.get('success') else ''
                    )
                    
                except Exception as e:
                    logger.error(f"❌ SMS notification failed for {template_name}: {str(e)}")
                    error_message += f"SMS failed: {str(e)}; "
                    success = False
            
            logger.info(f"🏁 NotificationService completed. Success: {success}, Error: {error_message}")
            return success, error_message
            
        except Exception as e:
            logger.error(f"💥 Critical error in NotificationService for {template_name}: {str(e)}")
            logger.error(f"📍 Critical error traceback:")
            import traceback
            logger.error(traceback.format_exc())
            return False, str(e)
    
    # Static notification methods (unchanged - these are used by Celery tasks)
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email when user first registers"""
        context = {
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        return NotificationService.send_notification(user, 'welcome', context)
    
    @staticmethod
    def send_profile_complete_email(user):
        """Send email when user completes profile"""
        context = {
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        }
        return NotificationService.send_notification(user, 'profile_complete', context)
    
    @staticmethod
    def send_subscription_created_email(user, subscription):
        """Send email when subscription is created (pending payment)"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': subscription.total_paid,
            'payment_url': f"{settings.FRONTEND_URL}/payment/{subscription.id}",
        }
        return NotificationService.send_notification(user, 'subscription_created', context)
    
    @staticmethod
    def send_payment_success_email(user, subscription, payment):
        """Send email when payment is successful"""
        context = {
            'subscription': subscription,
            'payment': payment,
            'plan_name': subscription.plan.name,
            'amount': payment.amount / 100,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
        }
        return NotificationService.send_notification(user, 'payment_success', context)
    
    @staticmethod
    def send_payment_failed_email(user, subscription, order):
        """Send email when payment fails"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': order.amount / 100,
            'retry_payment_url': f"{settings.FRONTEND_URL}/payment/{subscription.id}",
        }
        return NotificationService.send_notification(user, 'payment_failed', context)
    
    @staticmethod
    def send_leave_submitted_email(user, leave):
        """Send email when leave is submitted"""
        # To user (confirmation)
        context = {
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
        }
        NotificationService.send_notification(user, 'leave_submitted', context)
        
        # To mess owner (notification)
        from accounts.models import User
        mess_owners = User.objects.filter(user_type='mess_owner')
        
        owner_context = {
            'user_name': user.get_full_name() or user.username,
            'user_phone': user.phone,
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'reason': leave.reason,
            'dashboard_url': f"{settings.FRONTEND_URL}/owner/leaves",
        }
        
        for owner in mess_owners:
            NotificationService.send_notification(owner, 'new_leave_request', owner_context)
    
    @staticmethod
    def send_leave_approved_email(user, leave):
        """Send email when leave is approved"""
        context = {
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        return NotificationService.send_notification(user, 'leave_approved', context)
    
    @staticmethod
    def send_leave_rejected_email(user, leave):
        """Send email when leave is rejected"""
        context = {
            'leave': leave,
            'leave_days': leave.duration_days,
            'start_date': leave.leave_start_date,
            'end_date': leave.leave_end_date,
            'admin_comment': leave.admin_comment,
        }
        return NotificationService.send_notification(user, 'leave_rejected', context)
    
    @staticmethod
    def send_new_user_joined_email(mess_owners, user, subscription):
        """Send email to mess owners when new user joins"""
        context = {
            'new_user_name': user.get_full_name() or user.username,
            'new_user_phone': user.phone,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date,
            'dashboard_url': f"{settings.FRONTEND_URL}/owner/users",
        }
        
        for owner in mess_owners:
            NotificationService.send_notification(owner, 'new_user_joined', context)
    
    @staticmethod
    def send_subscription_cancelled_email(user, subscription):
        """Send email when subscription is cancelled"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'cancelled_date': subscription.cancelled_at.strftime('%B %d, %Y') if subscription.cancelled_at else 'Today',
            'refund_amount': subscription.refund_amount_calculated / 100 if subscription.refund_amount_calculated else 0,
            'refund_status': subscription.get_refund_status_display() if subscription.refund_status else 'No refund',
        }
        return NotificationService.send_notification(user, 'subscription_cancelled', context)
    
    @staticmethod
    def send_subscription_expiring_email(user, subscription):
        """Send email when subscription is about to expire"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expiry_date': subscription.adjusted_end_date,
            'renew_url': f"{settings.FRONTEND_URL}/renew/{subscription.id}",
        }
        return NotificationService.send_notification(user, 'subscription_expiring', context)
    
    @staticmethod
    def send_subscription_expired_email(user, subscription):
        """Send email when subscription has expired"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'expired_date': subscription.adjusted_end_date,
            'renew_url': f"{settings.FRONTEND_URL}/plans",
        }
        return NotificationService.send_notification(user, 'subscription_expired', context)
    
    @staticmethod
    def send_subscription_renewed_email(user, subscription):
        """Send email when subscription is renewed"""
        context = {
            'new_subscription': subscription,
            'plan_name': subscription.plan.name,
            'start_date': subscription.start_date,
            'end_date': subscription.adjusted_end_date,
            'amount': subscription.total_paid,
        }
        return NotificationService.send_notification(user, 'subscription_renewed', context)
    
    @staticmethod
    def send_payment_reminder_email(user, subscription):
        """Send payment reminder for pending subscription"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': subscription.total_paid,
            'payment_url': f"{settings.FRONTEND_URL}/payment/{subscription.id}",
            'days_pending': (timezone.now().date() - subscription.created_at.date()).days,
        }
        return NotificationService.send_notification(user, 'payment_reminder', context)
    
    @staticmethod
    def send_password_reset_email(user, uidb64, token):
        """Send password reset email"""
        context = {
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/",
        }
        return NotificationService.send_notification(user, 'password_reset', context)
    
    @staticmethod
    def send_password_changed_email(user):
        """Send password changed confirmation email"""
        context = {
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        return NotificationService.send_notification(user, 'password_changed', context)
    
    @staticmethod
    def send_refund_processed_email(user, refund_request):
        """Send email when refund is approved/processed"""
        context = {
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount,  
            'processed_date': refund_request.processed_at.strftime('%B %d, %Y') if refund_request.processed_at else 'Today',
            'refund_id': refund_request.id,
            'admin_comment': refund_request.admin_comment,
        }
        return NotificationService.send_notification(user, 'refund_processed', context)
    
    @staticmethod
    def send_refund_rejected_email(user, refund_request):
        """Send email when refund is rejected"""
        context = {
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount, 
            'admin_comment': refund_request.admin_comment,
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'refund_rejected', context)
    
    # SMS Auth methods
    @staticmethod
    def send_otp_sms(user, otp):
        """Send OTP via SMS"""
        context = {'otp': otp}
        return NotificationService.send_notification(user, 'otp_verification', context, channel='sms')
    
    @staticmethod
    def send_password_reset_otp_sms(user, otp):
        """Send password reset OTP via SMS"""
        context = {'otp': otp}
        return NotificationService.send_notification(user, 'password_reset_otp', context, channel='sms')
    
    @staticmethod
    def send_login_verification_sms(user, code):
        """Send login verification code via SMS"""
        context = {'verification_code': code}
        return NotificationService.send_notification(user, 'login_verification', context, channel='sms')
    
    @staticmethod
    def send_security_alert_sms(user, alert_message):
        """Send security alert via SMS"""
        context = {'alert_message': alert_message}
        return NotificationService.send_notification(user, 'security_alert', context, channel='sms')


# Updated convenience functions with async support
def send_welcome_email(user):
    logger.info(f"🎉 send_welcome_email called for {user.email}, _ASYNC: {_ASYNC}")
    if _ASYNC:
        try:
            from notifications.tasks import async_send_welcome_email
            task = async_send_welcome_email.delay(user.id)
            logger.info(f"🚀 Welcome email queued via Celery: {task.id}")
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue welcome email task: {str(e)}")
            # Fallback to sync
            return NotificationService.send_welcome_email(user)
    return NotificationService.send_welcome_email(user)

def send_profile_complete_email(user):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_profile_complete_email
            async_send_profile_complete_email.delay(user.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue profile complete email task: {str(e)}")
            return NotificationService.send_profile_complete_email(user)
    return NotificationService.send_profile_complete_email(user)

def send_subscription_created_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_subscription_created_email
            async_send_subscription_created_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue subscription created email task: {str(e)}")
            return NotificationService.send_subscription_created_email(user, subscription)
    return NotificationService.send_subscription_created_email(user, subscription)

def send_payment_success_email(user, subscription, payment):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_payment_success_email
            async_send_payment_success_email.delay(user.id, subscription.id, payment.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue payment success email task: {str(e)}")
            return NotificationService.send_payment_success_email(user, subscription, payment)
    return NotificationService.send_payment_success_email(user, subscription, payment)

def send_payment_failed_email(user, subscription, order):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_payment_failed_email
            async_send_payment_failed_email.delay(user.id, subscription.id, order.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue payment failed email task: {str(e)}")
            return NotificationService.send_payment_failed_email(user, subscription, order)
    return NotificationService.send_payment_failed_email(user, subscription, order)

def send_leave_submitted_email(user, leave):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_leave_submitted_email
            async_send_leave_submitted_email.delay(user.id, leave.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue leave submitted email task: {str(e)}")
            return NotificationService.send_leave_submitted_email(user, leave)
    return NotificationService.send_leave_submitted_email(user, leave)

def send_leave_approved_email(user, leave):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_leave_approved_email
            async_send_leave_approved_email.delay(user.id, leave.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue leave approved email task: {str(e)}")
            return NotificationService.send_leave_approved_email(user, leave)
    return NotificationService.send_leave_approved_email(user, leave)

def send_leave_rejected_email(user, leave):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_leave_rejected_email
            async_send_leave_rejected_email.delay(user.id, leave.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue leave rejected email task: {str(e)}")
            return NotificationService.send_leave_rejected_email(user, leave)
    return NotificationService.send_leave_rejected_email(user, leave)

def send_new_user_joined_email(mess_owners, user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_new_user_joined_email
            mess_owner_ids = [owner.id for owner in mess_owners]
            async_send_new_user_joined_email.delay(mess_owner_ids, user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue new user joined email task: {str(e)}")
            return NotificationService.send_new_user_joined_email(mess_owners, user, subscription)
    return NotificationService.send_new_user_joined_email(mess_owners, user, subscription)

def send_subscription_cancelled_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_subscription_cancelled_email
            async_send_subscription_cancelled_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue subscription cancelled email task: {str(e)}")
            return NotificationService.send_subscription_cancelled_email(user, subscription)
    return NotificationService.send_subscription_cancelled_email(user, subscription)

def send_subscription_expiring_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_subscription_expiring_email
            async_send_subscription_expiring_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue subscription expiring email task: {str(e)}")
            return NotificationService.send_subscription_expiring_email(user, subscription)
    return NotificationService.send_subscription_expiring_email(user, subscription)

def send_subscription_expired_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_subscription_expired_email
            async_send_subscription_expired_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue subscription expired email task: {str(e)}")
            return NotificationService.send_subscription_expired_email(user, subscription)
    return NotificationService.send_subscription_expired_email(user, subscription)

def send_subscription_renewed_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_subscription_renewed_email
            async_send_subscription_renewed_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue subscription renewed email task: {str(e)}")
            return NotificationService.send_subscription_renewed_email(user, subscription)
    return NotificationService.send_subscription_renewed_email(user, subscription)

def send_payment_reminder_email(user, subscription):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_payment_reminder_email
            async_send_payment_reminder_email.delay(user.id, subscription.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue payment reminder email task: {str(e)}")
            return NotificationService.send_payment_reminder_email(user, subscription)
    return NotificationService.send_payment_reminder_email(user, subscription)

def send_password_reset_email(user, uidb64, token):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_password_reset_email
            async_send_password_reset_email.delay(user.id, uidb64, token)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue password reset email task: {str(e)}")
            return NotificationService.send_password_reset_email(user, uidb64, token)
    return NotificationService.send_password_reset_email(user, uidb64, token)

def send_password_changed_email(user):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_password_changed_email
            async_send_password_changed_email.delay(user.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue password changed email task: {str(e)}")
            return NotificationService.send_password_changed_email(user)
    return NotificationService.send_password_changed_email(user)

def send_refund_processed_email(user, refund_request):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_refund_processed_email
            async_send_refund_processed_email.delay(user.id, refund_request.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue refund processed email task: {str(e)}")
            return NotificationService.send_refund_processed_email(user, refund_request)
    return NotificationService.send_refund_processed_email(user, refund_request)

def send_refund_rejected_email(user, refund_request):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_refund_rejected_email
            async_send_refund_rejected_email.delay(user.id, refund_request.id)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue refund rejected email task: {str(e)}")
            return NotificationService.send_refund_rejected_email(user, refund_request)
    return NotificationService.send_refund_rejected_email(user, refund_request)

# SMS Auth convenience functions
def send_otp_sms(user, otp):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_otp_sms
            async_send_otp_sms.delay(user.id, otp)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue OTP SMS task: {str(e)}")
            return NotificationService.send_otp_sms(user, otp)
    return NotificationService.send_otp_sms(user, otp)

def send_password_reset_otp_sms(user, otp):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_password_reset_otp_sms
            async_send_password_reset_otp_sms.delay(user.id, otp)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue password reset OTP SMS task: {str(e)}")
            return NotificationService.send_password_reset_otp_sms(user, otp)
    return NotificationService.send_password_reset_otp_sms(user, otp)

def send_login_verification_sms(user, code):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_login_verification_sms
            async_send_login_verification_sms.delay(user.id, code)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue login verification SMS task: {str(e)}")
            return NotificationService.send_login_verification_sms(user, code)
    return NotificationService.send_login_verification_sms(user, code)

def send_security_alert_sms(user, alert_message):
    if _ASYNC:
        try:
            from notifications.tasks import async_send_security_alert_sms
            async_send_security_alert_sms.delay(user.id, alert_message)
            return True, ""
        except Exception as e:
            logger.error(f"❌ Failed to queue security alert SMS task: {str(e)}")
            return NotificationService.send_security_alert_sms(user, alert_message)
    return NotificationService.send_security_alert_sms(user, alert_message)
