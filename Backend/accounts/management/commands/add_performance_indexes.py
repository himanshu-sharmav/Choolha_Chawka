from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add database indexes for better query performance'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Adding performance indexes...")
        
        with connection.cursor() as cursor:
            indexes = [
                # User indexes
                ("CREATE INDEX IF NOT EXISTS idx_user_phone ON accounts_user(phone);", 
                 "User phone lookup"),
                
                ("CREATE INDEX IF NOT EXISTS idx_user_status ON accounts_user(status);", 
                 "User status filtering"),
                
                ("CREATE INDEX IF NOT EXISTS idx_user_phone_verified ON accounts_user(phone_verified);", 
                 "Phone verification status"),
                
                # Subscription indexes
                ("CREATE INDEX IF NOT EXISTS idx_subscription_status_date ON subscriptions_subscription(status, adjusted_end_date);", 
                 "Subscription expiry checks"),
                
                ("CREATE INDEX IF NOT EXISTS idx_subscription_user_status ON subscriptions_subscription(user_id, status);", 
                 "User subscription lookups"),
                
                # OTP attempt indexes (if still using these tables)
                ("CREATE INDEX IF NOT EXISTS idx_otp_attempt_user_time ON accounts_otpverificationattempt(user_id, attempt_time);", 
                 "OTP attempt tracking"),
                
                ("CREATE INDEX IF NOT EXISTS idx_otp_throttle_phone ON accounts_otpthrottle(phone, last_sent);", 
                 "OTP throttling"),
            ]
            
            for sql, description in indexes:
                try:
                    self.stdout.write(f"  Creating index: {description}...")
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f"    ✅ {description}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    ⚠️  {description}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Index creation complete!"))
        self.stdout.write("\n💡 Tip: Run ANALYZE to update query planner statistics:")
        self.stdout.write("   psql -c 'ANALYZE;'")
