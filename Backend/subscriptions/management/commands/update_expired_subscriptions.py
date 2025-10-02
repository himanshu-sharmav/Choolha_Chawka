from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription
from notifications.services import send_subscription_expired_email


class Command(BaseCommand):
    help = 'Update subscription statuses to EXPIRED for subscriptions that have passed their end date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Send expiry notifications to users',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options['dry_run']
        send_notifications = options['send_notifications']
        
        # Find subscriptions that should be expired but are still active
        expired_subscriptions = Subscription.objects.filter(
            status='ACTIVE',
            adjusted_end_date__lte=today
        ).select_related('user', 'plan')
        
        count = expired_subscriptions.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired subscriptions found.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {count} subscriptions that should be expired:')
        )
        
        updated_count = 0
        notification_count = 0
        
        for subscription in expired_subscriptions:
            days_overdue = (today - subscription.adjusted_end_date).days
            
            self.stdout.write(
                f'  - User: {subscription.user.username} | '
                f'End Date: {subscription.adjusted_end_date} | '
                f'Days Overdue: {days_overdue}'
            )
            
            if not dry_run:
                # Update subscription status
                subscription.status = 'EXPIRED'
                subscription.save()
                updated_count += 1
                
                # Send notification if requested
                if send_notifications:
                    try:
                        send_subscription_expired_email(subscription.user, subscription)
                        notification_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'    ✅ Sent expiry notification to {subscription.user.username}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'    ❌ Failed to send notification to {subscription.user.username}: {e}')
                        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\nDRY RUN: Would update {count} subscriptions to EXPIRED status')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Updated {updated_count} subscriptions to EXPIRED status')
            )
            if send_notifications:
                self.stdout.write(
                    self.style.SUCCESS(f'📧 Sent {notification_count} expiry notifications')
                )
