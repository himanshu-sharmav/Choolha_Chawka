from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription
from notifications.services import send_subscription_expiring_email, send_subscription_expired_email

class Command(BaseCommand):
    help = 'Send subscription expiry notifications'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Send expiring notifications (3 days before expiry)
        expiring_date = today + timedelta(days=3)
        expiring_subscriptions = Subscription.objects.select_related('user', 'plan').filter(
            status='ACTIVE',
            adjusted_end_date=expiring_date
        )
        
        expiring_count = 0
        for subscription in expiring_subscriptions:
            try:
                send_subscription_expiring_email(subscription.user, subscription)
                expiring_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Sent expiring notification to {subscription.user.username}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send expiring notification to {subscription.user.username}: {e}')
                )
        
        # Send expired notifications (for subscriptions that expired today or before)
        expired_subscriptions = Subscription.objects.select_related('user', 'plan').filter(
            status='ACTIVE',
            adjusted_end_date__lte=today
        )
        
        expired_count = 0
        for subscription in expired_subscriptions:
            try:
                # Update subscription status
                subscription.status = 'EXPIRED'
                subscription.save()
                
                send_subscription_expired_email(subscription.user, subscription)
                expired_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Sent expired notification to {subscription.user.username}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send expired notification to {subscription.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent {expiring_count} expiring and {expired_count} expired notifications')
        )
