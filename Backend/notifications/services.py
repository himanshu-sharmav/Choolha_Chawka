import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from core.sms import send_sms  
from .models import NotificationTemplate, NotificationLog
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationService:
    
    @staticmethod
    def send_notification(user, notification_type, context_data=None, recipient_email=None, recipient_phone=None):
        try:
            # Get template
            template = NotificationTemplate.objects.get(
                name=notification_type, 
                is_active=True
            )
            
            context_data = context_data or {}
            context_data.update({
                'user': user,
                'user_name': user.get_full_name() or user.username,
                'platform_name': 'Choolha Chawka',
            })
            
            # Determine recipients
            email = recipient_email or user.email
            phone = recipient_phone or user.phone
            
            success = True
            error_message = ""
            
            # Send Email using Django's send_mail (now with SendGrid SMTP)
            if template.channel in ['email', 'both'] and email:
                try:
                    subject = Template(template.subject).render(Context(context_data))
                    message = Template(template.email_template).render(Context(context_data))
                    
                    # 🔥 Use Django's send_mail with SendGrid SMTP backend
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    
                    status = 'sent'
                    
                    # Log email notification
                    NotificationLog.objects.create(
                        user=user,
                        notification_type=notification_type,
                        channel='email',
                        recipient_email=email,
                        subject=subject,
                        message=message,
                        status=status
                    )
                    
                except Exception as e:
                    logger.error(f"Email notification failed: {str(e)}")
                    error_message += f"Email failed: {str(e)}; "
                    success = False
                    
                    # Log failed email notification
                    NotificationLog.objects.create(
                        user=user,
                        notification_type=notification_type,
                        channel='email',
                        recipient_email=email,
                        subject=subject if 'subject' in locals() else '',
                        message=message if 'message' in locals() else '',
                        status='failed',
                        error_message=str(e)
                    )
            
            # Send SMS (unchanged)
            if template.channel in ['sms', 'both'] and phone:
                try:
                    sms_message = Template(template.sms_template).render(Context(context_data))
                    
                    sms_response = send_sms(phone, sms_message)
                    
                    if sms_response.get('success'):
                        status = 'sent'
                    else:
                        status = 'failed'
                        error_message += f"SMS failed: {sms_response.get('error', 'Unknown error')}; "
                        success = False
                    
                    # Log SMS notification
                    NotificationLog.objects.create(
                        user=user,
                        notification_type=notification_type,
                        channel='sms',
                        recipient_phone=phone,
                        message=sms_message,
                        status=status,
                        error_message=sms_response.get('error', '') if not sms_response.get('success') else ''
                    )
                    
                except Exception as e:
                    logger.error(f"SMS notification failed: {str(e)}")
                    error_message += f"SMS failed: {str(e)}; "
                    success = False
            
            return success, error_message
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template not found: {notification_type}")
            return False, f"Template not found: {notification_type}"
        except Exception as e:
            logger.error(f"Notification service error: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email when user first registers"""
        context = {
            'login_url': f"{settings.FRONTEND_URL}/login",
            'support_email': settings.SUPPORT_EMAIL,
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
        # Find mess owners (users with user_type='mess_owner')
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
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'subscription_cancelled', context)        
    
    @staticmethod
    def send_payment_failed_email(user, subscription, order):
        """Send email when payment fails"""
        context = {
            'subscription': subscription,
            'plan_name': subscription.plan.name,
            'amount': order.amount / 100,
            'retry_payment_url': f"{settings.FRONTEND_URL}/payment/{subscription.id}",
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'payment_failed', context)

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
    def send_refund_processed_email(user, refund_request):
        """Send email when refund is processed"""
        context = {
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount / 100,
            'processed_date': refund_request.processed_at.strftime('%B %d, %Y') if refund_request.processed_at else 'Today',
            'refund_id': refund_request.gateway_refund_id or refund_request.refund_transaction_id,
        }
        return NotificationService.send_notification(user, 'refund_processed', context)
    
    @staticmethod
    def send_refund_rejected_email(user, refund_request):
        """Send email when refund is rejected"""
        context = {
            'refund_request': refund_request,
            'subscription': refund_request.subscription,
            'plan_name': refund_request.subscription.plan.name,
            'refund_amount': refund_request.amount / 100,
            'admin_comment': refund_request.admin_comment,
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'refund_rejected', context)
    
    @staticmethod
    def send_password_reset_email(user, uidb64, token):
        """Send password reset email"""
        context = {
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/",
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'password_reset', context)

    @staticmethod
    def send_password_changed_email(user):
        """Send password changed confirmation email"""
        context = {
            'login_url': f"{settings.FRONTEND_URL}/login",
            'support_email': settings.SUPPORT_EMAIL,
        }
        return NotificationService.send_notification(user, 'password_changed', context)

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
    def send_subscription_renewed_email(user, old_subscription, new_subscription):
        """Send email when subscription is renewed"""
        context = {
            'old_subscription': old_subscription,
            'new_subscription': new_subscription,
            'plan_name': new_subscription.plan.name,
            'start_date': new_subscription.start_date,
            'end_date': new_subscription.adjusted_end_date,
            'amount': new_subscription.total_paid,
        }
        return NotificationService.send_notification(user, 'subscription_renewed', context)


# Convenience functions
def send_welcome_email(user):
    return NotificationService.send_welcome_email(user)

def send_profile_complete_email(user):
    return NotificationService.send_profile_complete_email(user)

def send_subscription_created_email(user, subscription):
    return NotificationService.send_subscription_created_email(user, subscription)

def send_payment_success_email(user, subscription, payment):
    return NotificationService.send_payment_success_email(user, subscription, payment)

def send_leave_submitted_email(user, leave):
    return NotificationService.send_leave_submitted_email(user, leave)

def send_leave_approved_email(user, leave):
    return NotificationService.send_leave_approved_email(user, leave)

def send_leave_rejected_email(user, leave):
    return NotificationService.send_leave_rejected_email(user, leave)

def send_new_user_joined_email(mess_owners, user, subscription):
    return NotificationService.send_new_user_joined_email(mess_owners, user, subscription)

def send_subscription_cancelled_email(user, subscription):
    return NotificationService.send_subscription_cancelled_email(user, subscription)

def send_payment_failed_email(user, subscription, order):
    return NotificationService.send_payment_failed_email(user, subscription, order)

def send_subscription_expiring_email(user, subscription):
    return NotificationService.send_subscription_expiring_email(user, subscription)

def send_refund_processed_email(user, refund_request):
    return NotificationService.send_refund_processed_email(user, refund_request)

def send_refund_rejected_email(user, refund_request):
    return NotificationService.send_refund_rejected_email(user, refund_request)

def send_password_reset_email(user, uidb64, token):
    return NotificationService.send_password_reset_email(user, uidb64, token)

def send_password_changed_email(user):
    return NotificationService.send_password_changed_email(user)

def send_payment_reminder_email(user, subscription):
    return NotificationService.send_payment_reminder_email(user, subscription)

def send_subscription_expired_email(user, subscription):
    return NotificationService.send_subscription_expired_email(user, subscription)

def send_subscription_renewed_email(user, old_subscription, new_subscription):
    return NotificationService.send_subscription_renewed_email(user, old_subscription, new_subscription)
