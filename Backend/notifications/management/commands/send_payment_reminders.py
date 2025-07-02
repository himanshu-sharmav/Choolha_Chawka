from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription
from notifications.services import send_payment_reminder_email

class Command(BaseCommand):
    help = 'Send payment reminders for pending subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Send reminders for subscriptions pending for X days'
        )

    def handle(self, *args, **options):
        days_ago = timezone.now() - timedelta(days=options['days'])
        
        pending_subscriptions = Subscription.objects.select_related('user', 'plan').filter(
            status='PENDING_PAYMENT',
            created_at__lte=days_ago
        )
        
        sent_count = 0
        for subscription in pending_subscriptions:
            try:
                send_payment_reminder_email(subscription.user, subscription)
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Sent payment reminder to {subscription.user.username}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send to {subscription.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {sent_count} payment reminders')
        )
