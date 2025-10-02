# Subscription Expiry Management

This document explains how subscription expiry is handled in the Choolha Chawka application.

## Problem

Subscriptions were not automatically updating to `EXPIRED` status when their end date passed. This happened because:

1. The model's `save()` method only runs when subscriptions are explicitly modified
2. No scheduled tasks were running to check for expired subscriptions
3. The existing management command had a bug in its date logic

## Solution

I've implemented a comprehensive solution with multiple layers:

### 1. Management Commands

#### `update_expired_subscriptions`
- **Location**: `Backend/subscriptions/management/commands/update_expired_subscriptions.py`
- **Purpose**: Updates subscription statuses to EXPIRED for subscriptions past their end date
- **Usage**:
  ```bash
  python manage.py update_expired_subscriptions
  python manage.py update_expired_subscriptions --dry-run  # Preview changes
  python manage.py update_expired_subscriptions --send-notifications  # Send emails
  ```

#### `send_expiry_notifications` (Fixed)
- **Location**: `Backend/notifications/management/commands/send_expiry_notifications.py`
- **Purpose**: Sends notifications for expiring and expired subscriptions
- **Fix**: Changed from looking for subscriptions expired "yesterday" to subscriptions expired "today or before"

### 2. Celery Tasks

#### `update_expired_subscriptions` (Celery Task)
- **Location**: `Backend/subscriptions/tasks.py`
- **Schedule**: Every hour
- **Purpose**: Automatically update expired subscriptions

#### `send_expiry_notifications` (Celery Task)
- **Schedule**: Daily at midnight
- **Purpose**: Send expiry notifications

#### `cleanup_expired_subscriptions` (Celery Task)
- **Schedule**: Weekly (can be configured)
- **Purpose**: Clean up very old expired subscriptions

### 3. Celery Beat Configuration

Added to `config/settings.py`:
```python
CELERY_BEAT_SCHEDULE = {
    'update-expired-subscriptions': {
        'task': 'subscriptions.tasks.update_expired_subscriptions',
        'schedule': 60.0 * 60,  # Run every hour
    },
    'send-expiry-notifications': {
        'task': 'notifications.tasks.send_expiry_notifications',
        'schedule': 60.0 * 60 * 24,  # Run daily at midnight
    },
}
CELERY_TIMEZONE = 'Asia/Kolkata'
```

### 4. Updated Procfile

Added Celery Beat process:
```
web:    gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A config worker --loglevel=info
beat:    celery -A config beat --loglevel=info
```

### 5. Manual Script

#### `update_expired_subscriptions.py`
- **Location**: `Backend/update_expired_subscriptions.py`
- **Purpose**: Standalone script to manually update expired subscriptions
- **Usage**:
  ```bash
  python update_expired_subscriptions.py
  python update_expired_subscriptions.py --notifications
  ```

## How to Use

### Immediate Fix (Run Now)

To immediately fix all expired subscriptions:

```bash
cd Backend
python manage.py update_expired_subscriptions --send-notifications
```

### Production Deployment

1. **Deploy the updated code** with the new Celery Beat configuration
2. **Start Celery Beat** process (already configured in Procfile)
3. **Monitor the logs** to ensure tasks are running correctly

### Local Development

```bash
# Start Celery Beat (in a separate terminal)
celery -A config beat --loglevel=info

# Start Celery Worker (in another terminal)
celery -A config worker --loglevel=info

# Run Django server
python manage.py runserver
```

### Manual Testing

```bash
# Test the management command
python manage.py update_expired_subscriptions --dry-run

# Test with notifications
python manage.py update_expired_subscriptions --send-notifications

# Test the manual script
python update_expired_subscriptions.py --notifications
```

## Monitoring

### Check Task Status

```bash
# Check Celery Beat status
celery -A config beat --loglevel=info

# Check Celery Worker status
celery -A config worker --loglevel=info

# Monitor task execution
celery -A config events
```

### Database Queries

```python
# Check expired subscriptions
from subscriptions.models import Subscription
from django.utils import timezone

today = timezone.now().date()
expired_but_active = Subscription.objects.filter(
    status='ACTIVE',
    adjusted_end_date__lt=today
)
print(f"Found {expired_but_active.count()} expired but active subscriptions")
```

## Troubleshooting

### Common Issues

1. **Celery Beat not running**: Ensure the `beat` process is started
2. **Tasks not executing**: Check Redis connection and Celery worker status
3. **Database connection issues**: Verify database credentials and connectivity

### Logs to Check

- Celery Beat logs: Look for scheduled task execution
- Celery Worker logs: Look for task completion
- Django logs: Look for any errors in the management commands

## Future Improvements

1. **Add more granular scheduling**: Different schedules for different types of notifications
2. **Implement subscription archiving**: Move very old expired subscriptions to archive tables
3. **Add metrics and monitoring**: Track subscription expiry patterns
4. **Implement retry logic**: Retry failed notification sends
5. **Add admin interface**: Web interface to manually trigger expiry updates

## Files Modified/Created

### New Files
- `Backend/subscriptions/management/commands/update_expired_subscriptions.py`
- `Backend/subscriptions/tasks.py`
- `Backend/update_expired_subscriptions.py`
- `Backend/subscriptions/management/__init__.py`
- `Backend/subscriptions/management/commands/__init__.py`

### Modified Files
- `Backend/notifications/management/commands/send_expiry_notifications.py` (Fixed date logic)
- `Backend/config/settings.py` (Added Celery Beat configuration)
- `Backend/Procfile` (Added Celery Beat process)

## Testing

The solution has been designed to be safe and non-destructive:

1. **Dry-run mode**: Test changes without applying them
2. **Logging**: Comprehensive logging for monitoring
3. **Error handling**: Graceful error handling with detailed error messages
4. **Incremental updates**: Only updates subscriptions that actually need updating
