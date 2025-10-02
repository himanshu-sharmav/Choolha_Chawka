#!/usr/bin/env python
"""
Manual script to update expired subscriptions
Run this script to immediately update all expired subscriptions
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from subscriptions.models import Subscription
from django.utils import timezone
from notifications.services import send_subscription_expired_email


def update_expired_subscriptions(send_notifications=False):
    """Update expired subscriptions and optionally send notifications"""
    today = timezone.now().date()
    
    # Find subscriptions that should be expired but are still active
    expired_subscriptions = Subscription.objects.filter(
        status='ACTIVE',
        adjusted_end_date__lt=today
    ).select_related('user', 'plan')
    
    count = expired_subscriptions.count()
    
    if count == 0:
        print("✅ No expired subscriptions found.")
        return
    
    print(f"🔍 Found {count} subscriptions that should be expired:")
    
    updated_count = 0
    notification_count = 0
    
    for subscription in expired_subscriptions:
        days_overdue = (today - subscription.adjusted_end_date).days
        
        print(f"  📅 User: {subscription.user.username} | "
              f"End Date: {subscription.adjusted_end_date} | "
              f"Days Overdue: {days_overdue}")
        
        # Update subscription status
        subscription.status = 'EXPIRED'
        subscription.save()
        updated_count += 1
        
        # Send notification if requested
        if send_notifications:
            try:
                send_subscription_expired_email(subscription.user, subscription)
                notification_count += 1
                print(f"    ✅ Sent expiry notification to {subscription.user.username}")
            except Exception as e:
                print(f"    ❌ Failed to send notification to {subscription.user.username}: {e}")
    
    print(f"\n✅ Updated {updated_count} subscriptions to EXPIRED status")
    if send_notifications:
        print(f"📧 Sent {notification_count} expiry notifications")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update expired subscriptions')
    parser.add_argument('--notifications', action='store_true', 
                       help='Send expiry notifications to users')
    
    args = parser.parse_args()
    
    print("🚀 Starting subscription expiry update...")
    update_expired_subscriptions(send_notifications=args.notifications)
    print("✅ Done!")
