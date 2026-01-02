from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPVerificationAttempt, OTPThrottle


class Command(BaseCommand):
    help = 'Clean up old OTP verification attempts and throttle records to save memory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete records older than this many days (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"🧹 Cleaning up OTP records older than {days} days (before {cutoff_date.date()})")
        
        # Clean up old verification attempts
        old_attempts = OTPVerificationAttempt.objects.filter(
            attempt_time__lt=cutoff_date
        )
        attempts_count = old_attempts.count()
        
        # Clean up old throttle records (older than 1 day)
        one_day_ago = timezone.now() - timedelta(days=1)
        old_throttles = OTPThrottle.objects.filter(
            last_sent__lt=one_day_ago
        )
        throttles_count = old_throttles.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n🔍 DRY RUN - Would delete:\n"
                    f"  - {attempts_count} OTP verification attempts\n"
                    f"  - {throttles_count} OTP throttle records\n"
                    f"  Total: {attempts_count + throttles_count} records"
                )
            )
        else:
            # Delete the records
            old_attempts.delete()
            old_throttles.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Deleted:\n"
                    f"  - {attempts_count} OTP verification attempts\n"
                    f"  - {throttles_count} OTP throttle records\n"
                    f"  Total: {attempts_count + throttles_count} records"
                )
            )
            
            # Show memory savings estimate
            estimated_bytes = (attempts_count + throttles_count) * 200  # Rough estimate
            estimated_kb = estimated_bytes / 1024
            estimated_mb = estimated_kb / 1024
            
            if estimated_mb > 1:
                self.stdout.write(
                    self.style.SUCCESS(f"💾 Estimated memory saved: ~{estimated_mb:.2f} MB")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"💾 Estimated memory saved: ~{estimated_kb:.2f} KB")
                )
