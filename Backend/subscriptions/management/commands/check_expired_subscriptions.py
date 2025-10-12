from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = 'Check for subscriptions that should be expired (debugging command)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        self.stdout.write(f"Today's date: {today}")
        self.stdout.write(f"Timezone: {timezone.get_current_timezone()}")
        
        # Check all active subscriptions
        active_subscriptions = Subscription.objects.filter(status='ACTIVE').select_related('user', 'plan')
        
        self.stdout.write(f"\n📊 Found {active_subscriptions.count()} active subscriptions:")
        
        expired_count = 0
        expiring_soon_count = 0
        
        for subscription in active_subscriptions:
            days_remaining = (subscription.adjusted_end_date - today).days
            
            if days_remaining < 0:
                expired_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ EXPIRED: {subscription.user.username} | "
                        f"Plan: {subscription.plan.name} | "
                        f"End Date: {subscription.adjusted_end_date} | "
                        f"Days Overdue: {abs(days_remaining)}"
                    )
                )
            elif days_remaining <= 3:
                expiring_soon_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  EXPIRING SOON: {subscription.user.username} | "
                        f"Plan: {subscription.plan.name} | "
                        f"End Date: {subscription.adjusted_end_date} | "
                        f"Days Remaining: {days_remaining}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ ACTIVE: {subscription.user.username} | "
                        f"Plan: {subscription.plan.name} | "
                        f"End Date: {subscription.adjusted_end_date} | "
                        f"Days Remaining: {days_remaining}"
                    )
                )
        
        # Check expired subscriptions
        expired_subscriptions = Subscription.objects.filter(status='EXPIRED').select_related('user', 'plan')
        
        self.stdout.write(f"\n📊 Found {expired_subscriptions.count()} already expired subscriptions:")
        
        for subscription in expired_subscriptions:
            days_since_expired = (today - subscription.adjusted_end_date).days
            self.stdout.write(
                f"🔴 {subscription.user.username} | "
                f"Plan: {subscription.plan.name} | "
                f"Expired: {subscription.adjusted_end_date} | "
                f"Days Since Expired: {days_since_expired}"
            )
        
        # Summary
        self.stdout.write(f"\n📈 SUMMARY:")
        self.stdout.write(f"   Active subscriptions: {active_subscriptions.count()}")
        self.stdout.write(f"   Should be expired: {expired_count}")
        self.stdout.write(f"   Expiring soon (≤3 days): {expiring_soon_count}")
        self.stdout.write(f"   Already expired: {expired_subscriptions.count()}")
        
        if expired_count > 0:
            self.stdout.write(
                self.style.ERROR(f"\n⚠️  ACTION NEEDED: {expired_count} subscriptions should be expired!")
            )
            self.stdout.write("Run: python manage.py update_expired_subscriptions --send-notifications")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ All subscriptions are properly managed!")
            )