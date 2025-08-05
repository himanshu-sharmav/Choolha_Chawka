from celery import shared_task
from django.contrib.auth import get_user_model
from notifications.services import NotificationService as NS

User = get_user_model()

def _get_user(pk):
    return User.objects.get(id=pk)

# Authentication and Profile Tasks
@shared_task
def async_send_welcome_email(user_id):
    NS.send_welcome_email(_get_user(user_id))

@shared_task
def async_send_profile_complete_email(user_id):
    NS.send_profile_complete_email(_get_user(user_id))

@shared_task
def async_send_password_changed_email(user_id):
    NS.send_password_changed_email(_get_user(user_id))

@shared_task
def async_send_password_reset_email(user_id, uidb64, token):
    NS.send_password_reset_email(_get_user(user_id), uidb64, token)

# Subscription Tasks
@shared_task
def async_send_subscription_created_email(user_id, subscription_id):
    from subscriptions.models import Subscription
    NS.send_subscription_created_email(
        _get_user(user_id),
        Subscription.objects.get(id=subscription_id)
    )

@shared_task
def async_send_subscription_cancelled_email(user_id, subscription_id):
    from subscriptions.models import Subscription
    NS.send_subscription_cancelled_email(
        _get_user(user_id),
        Subscription.objects.get(id=subscription_id)
    )

@shared_task
def async_send_subscription_renewed_email(user_id,sub_id):
    from subscriptions.models import Subscription
    NS.send_subscription_renewed_email(
        _get_user(user_id),
        Subscription.objects.get(id=sub_id)
    )

# Leave Management Tasks
@shared_task
def async_send_leave_submitted_email(user_id, leave_id):
    from subscriptions.models import Leave
    NS.send_leave_submitted_email(
        _get_user(user_id),
        Leave.objects.get(id=leave_id)
    )

@shared_task
def async_send_leave_approved_email(user_id, leave_id):
    from subscriptions.models import Leave
    NS.send_leave_approved_email(
        _get_user(user_id),
        Leave.objects.get(id=leave_id)
    )

@shared_task
def async_send_leave_rejected_email(user_id, leave_id):
    from subscriptions.models import Leave
    NS.send_leave_rejected_email(
        _get_user(user_id),
        Leave.objects.get(id=leave_id)
    )

# Payment Tasks
@shared_task
def async_send_payment_success_email(user_id, subscription_id, payment_id):
    from subscriptions.models import Subscription
    from payments.models import Payment
    NS.send_payment_success_email(
        _get_user(user_id),
        Subscription.objects.get(id=subscription_id),
        Payment.objects.get(id=payment_id)
    )

@shared_task
def async_send_payment_failed_email(user_id, subscription_id, order_id):
    from subscriptions.models import Subscription
    from payments.models import PaymentOrder
    NS.send_payment_failed_email(
        _get_user(user_id),
        Subscription.objects.get(id=subscription_id),
        PaymentOrder.objects.get(id=order_id)
    )

# Refund Tasks
@shared_task
def async_send_refund_processed_email(user_id, refund_id):
    from payments.models import RefundRequest
    NS.send_refund_processed_email(
        _get_user(user_id),
        RefundRequest.objects.get(id=refund_id)
    )

@shared_task
def async_send_refund_rejected_email(user_id, refund_id):
    from payments.models import RefundRequest
    NS.send_refund_rejected_email(
        _get_user(user_id),
        RefundRequest.objects.get(id=refund_id)
    )

# Mess Owner Notification Tasks
@shared_task
def async_send_new_user_joined_email(mess_owner_ids, user_id, subscription_id):
    from subscriptions.models import Subscription
    mess_owners = User.objects.filter(id__in=mess_owner_ids)
    user = _get_user(user_id)
    subscription = Subscription.objects.get(id=subscription_id)
    NS.send_new_user_joined_email(mess_owners, user, subscription)

# SMS Tasks
@shared_task
def async_send_otp_sms(user_id, otp):
    NS.send_otp_sms(_get_user(user_id), otp)

@shared_task
def async_send_password_reset_otp_sms(user_id, otp):
    NS.send_password_reset_otp_sms(_get_user(user_id), otp)
