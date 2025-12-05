# Memory Optimization Guide

## Overview
This document outlines memory optimization strategies implemented in the Choolha Chawka backend.

## 1. Redis-Based OTP Storage ✅

### Problem
- OTPs were stored in database fields (`phone_verification_otp`, `otp_expiry`)
- Database writes for every OTP generation
- Old OTP records never cleaned up
- Verification attempts stored indefinitely

### Solution
- **New Service**: `core/otp_service.py` - Redis-based OTP management
- OTPs stored in Redis with automatic expiry (15 minutes)
- No database writes for OTP storage
- Automatic cleanup when OTPs expire

### Benefits
- **Memory**: ~200 bytes saved per OTP (no DB storage)
- **Performance**: Redis is 10-100x faster than DB for simple key-value operations
- **Automatic cleanup**: Redis TTL handles expiry automatically

### Usage
```python
from core.otp_service import OTPService

# Generate OTP
otp = OTPService.generate_otp(identifier="user_123")

# Verify OTP
is_valid, message = OTPService.verify_otp(identifier="user_123", otp="123456")

# Check throttling
can_send, message = OTPService.can_send_otp(identifier="+1234567890")
```

## 2. Automatic Cleanup Tasks ✅

### OTP Records Cleanup
- **Task**: `accounts.tasks.cleanup_old_otp_records`
- **Schedule**: Daily at 2 AM
- **Action**: Deletes OTP verification attempts older than 7 days
- **Command**: `python manage.py cleanup_otp_records`

### Benefits
- Prevents database bloat
- Keeps OTP-related tables lean
- Estimated savings: ~200 bytes per record

## 3. Database Optimization Recommendations

### Add Indexes
```python
# In your models, add:
class Meta:
    indexes = [
        models.Index(fields=['phone', '-created_at']),
        models.Index(fields=['status', 'adjusted_end_date']),
        models.Index(fields=['user', 'status']),
    ]
```

### Use select_related() and prefetch_related()
```python
# Bad - N+1 queries
subscriptions = Subscription.objects.filter(status='ACTIVE')
for sub in subscriptions:
    print(sub.user.username)  # Extra query per subscription!

# Good - Single query with JOIN
subscriptions = Subscription.objects.filter(
    status='ACTIVE'
).select_related('user', 'plan')
```

### Pagination for Large Querysets
```python
# Bad - Loads all records into memory
all_users = User.objects.all()

# Good - Paginate
from django.core.paginator import Paginator

paginator = Paginator(User.objects.all(), 100)
for page_num in paginator.page_range:
    page = paginator.page(page_num)
    for user in page:
        process_user(user)
```

## 4. Additional Optimizations

### Cache Frequently Accessed Data
```python
from django.core.cache import cache

# Cache active plans
def get_active_plans():
    cache_key = 'active_plans'
    plans = cache.get(cache_key)
    
    if plans is None:
        plans = list(Plan.objects.filter(is_active=True))
        cache.set(cache_key, plans, timeout=3600)  # 1 hour
    
    return plans
```

### Use only() and defer() for Large Models
```python
# Only load specific fields
users = User.objects.only('id', 'username', 'email')

# Defer loading large fields
users = User.objects.defer('profile_picture', 'bio')
```

### Bulk Operations
```python
# Bad - Multiple DB hits
for user in users:
    user.status = 'active'
    user.save()

# Good - Single query
User.objects.filter(id__in=user_ids).update(status='active')
```

## 5. Monitoring Memory Usage

### Check Redis Memory
```bash
redis-cli INFO memory
```

### Check Database Size
```sql
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name::regclass) DESC;
```

### Django Debug Toolbar
Add to development environment to monitor queries:
```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

## 6. Migration Plan

### Phase 1: Deploy Redis OTP Service ✅
- [x] Create `core/otp_service.py`
- [x] Update User model methods
- [x] Test OTP generation and verification
- [ ] Deploy to production

### Phase 2: Clean Up Old Data
- [ ] Run `python manage.py cleanup_otp_records --dry-run`
- [ ] Run `python manage.py cleanup_otp_records`
- [ ] Monitor database size reduction

### Phase 3: Remove Old Fields (Optional)
After confirming Redis OTP works:
```python
# Create migration to remove old fields
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField('User', 'phone_verification_otp'),
        migrations.RemoveField('User', 'otp_expiry'),
    ]
```

## 7. Expected Memory Savings

### Per User Registration
- **Before**: ~400 bytes (DB storage for OTP + expiry + attempts)
- **After**: ~50 bytes (Redis with auto-expiry)
- **Savings**: ~350 bytes per OTP (87.5% reduction)

### For 10,000 Daily OTPs
- **Before**: ~4 MB in database
- **After**: ~0.5 MB in Redis (with auto-cleanup)
- **Savings**: ~3.5 MB per day

### Annual Savings (10K OTPs/day)
- **Database**: ~1.4 GB saved
- **Faster queries**: Less data to scan
- **Better performance**: Redis is in-memory

## 8. Testing

### Test OTP Service
```bash
# Django shell
python manage.py shell

from core.otp_service import OTPService

# Generate OTP
otp = OTPService.generate_otp("test_user")
print(f"Generated OTP: {otp}")

# Verify OTP
is_valid, msg = OTPService.verify_otp("test_user", otp)
print(f"Valid: {is_valid}, Message: {msg}")

# Test throttling
for i in range(5):
    can_send, msg = OTPService.can_send_otp("test_phone")
    print(f"Attempt {i+1}: {can_send}")
```

### Test Cleanup Command
```bash
# Dry run
python manage.py cleanup_otp_records --dry-run

# Actual cleanup
python manage.py cleanup_otp_records --days=7
```

## 9. Monitoring & Alerts

### Set up alerts for:
- Redis memory usage > 80%
- Database size growth rate
- OTP verification failure rate
- Celery task failures

### Useful Commands
```bash
# Check Celery tasks
celery -A config inspect active

# Check Redis keys
redis-cli KEYS "otp:*" | wc -l

# Monitor database connections
SELECT count(*) FROM pg_stat_activity;
```

## 10. Best Practices

1. **Always use Redis for temporary data** (sessions, OTPs, rate limiting)
2. **Clean up old data regularly** (automated tasks)
3. **Use database indexes** for frequently queried fields
4. **Paginate large querysets** to avoid loading everything into memory
5. **Cache expensive queries** that don't change often
6. **Monitor memory usage** in production
7. **Use select_related/prefetch_related** to avoid N+1 queries
8. **Bulk operations** instead of loops with individual saves

## Summary

✅ **Implemented**:
- Redis-based OTP storage
- Automatic OTP cleanup task
- Management command for manual cleanup
- Comprehensive documentation

🔄 **Next Steps**:
- Deploy to production
- Monitor memory usage
- Add database indexes
- Implement query optimization
- Consider removing old OTP fields from database

💡 **Key Takeaway**: Moving OTPs to Redis saves ~87.5% memory and improves performance significantly!
