from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription
from notifications.services import send_subscription_expired_email
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_expired_subscriptions():
    """
    Celery task to update subscription statuses to EXPIRED
    Runs every hour to catch expired subscriptions
    """
    logger.info("🔄 Starting update_expired_subscriptions task")
    
    try:
        today = timezone.now().date()
        
        # Find subscriptions that should be expired but are still active
        expired_subscriptions = Subscription.objects.filter(
            status='ACTIVE',
            adjusted_end_date__lte=today
        ).select_related('user', 'plan')
        
        count = expired_subscriptions.count()
        
        if count == 0:
            logger.info("✅ No expired subscriptions found")
            return {'updated': 0, 'message': 'No expired subscriptions found'}
        
        logger.info(f"🔍 Found {count} subscriptions that should be expired")
        
        updated_count = 0
        for subscription in expired_subscriptions:
            days_overdue = (today - subscription.adjusted_end_date).days
            
            logger.info(
                f"📅 Updating subscription for {subscription.user.username} "
                f"(expired {days_overdue} days ago)"
            )
            
            # Update subscription status
            subscription.status = 'EXPIRED'
            subscription.save()
            updated_count += 1
        
        logger.info(f"✅ Successfully updated {updated_count} subscriptions to EXPIRED")
        
        return {
            'updated': updated_count,
            'message': f'Updated {updated_count} subscriptions to EXPIRED status'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in update_expired_subscriptions task: {str(e)}")
        raise


@shared_task
def send_expiry_notifications():
    """
    Celery task to send expiry notifications
    Runs daily to send notifications for expiring and expired subscriptions
    """
    logger.info("📧 Starting send_expiry_notifications task")
    
    try:
        # Call the management command from notifications app
        call_command('send_expiry_notifications')
        
        logger.info("✅ Successfully completed send_expiry_notifications task")
        
        return {
            'success': True,
            'message': 'Expiry notifications sent successfully'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in send_expiry_notifications task: {str(e)}")
        raise


@shared_task
def cleanup_expired_subscriptions():
    """
    Celery task to clean up old expired subscriptions
    Runs weekly to archive or clean up very old expired subscriptions
    """
    logger.info("🧹 Starting cleanup_expired_subscriptions task")
    
    try:
        today = timezone.now().date()
        # Find subscriptions expired more than 90 days ago
        old_expired_date = today - timedelta(days=90)
        
        old_expired_subscriptions = Subscription.objects.filter(
            status='EXPIRED',
            adjusted_end_date__lt=old_expired_date
        )
        
        count = old_expired_subscriptions.count()
        
        if count == 0:
            logger.info("✅ No old expired subscriptions found for cleanup")
            return {'cleaned': 0, 'message': 'No old expired subscriptions found'}
        
        logger.info(f"🔍 Found {count} old expired subscriptions for cleanup")
        
        # For now, just log them. In the future, you might want to:
        # - Archive them to a separate table
        # - Delete them if they're very old
        # - Move them to cold storage
        
        for subscription in old_expired_subscriptions:
            days_old = (today - subscription.adjusted_end_date).days
            logger.info(
                f"📅 Old expired subscription: {subscription.user.username} "
                f"(expired {days_old} days ago)"
            )
        
        logger.info(f"✅ Cleanup task completed for {count} old expired subscriptions")
        
        return {
            'cleaned': count,
            'message': f'Found {count} old expired subscriptions for cleanup'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in cleanup_expired_subscriptions task: {str(e)}")
        raise
