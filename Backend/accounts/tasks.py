from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPVerificationAttempt, OTPThrottle
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_otp_records():
    """
    Celery task to clean up old OTP-related records
    Runs daily to keep database lean
    """
    logger.info("🧹 Starting cleanup_old_otp_records task")
    
    try:
        # Delete attempts older than 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        old_attempts = OTPVerificationAttempt.objects.filter(
            attempt_time__lt=seven_days_ago
        )
        attempts_count = old_attempts.count()
        old_attempts.delete()
        
        # Delete throttle records older than 1 day
        one_day_ago = timezone.now() - timedelta(days=1)
        old_throttles = OTPThrottle.objects.filter(
            last_sent__lt=one_day_ago
        )
        throttles_count = old_throttles.count()
        old_throttles.delete()
        
        total_deleted = attempts_count + throttles_count
        
        logger.info(
            f"✅ Cleaned up {total_deleted} OTP records "
            f"({attempts_count} attempts, {throttles_count} throttles)"
        )
        
        return {
            'deleted': total_deleted,
            'attempts': attempts_count,
            'throttles': throttles_count,
            'message': f'Cleaned up {total_deleted} old OTP records'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in cleanup_old_otp_records task: {str(e)}")
        raise
