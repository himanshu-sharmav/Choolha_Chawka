from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Plan(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('mess', 'Mess Eating'),
        ('tiffin', 'Tiffin Delivery'),
    ]
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE_CHOICES)
    base_price = models.PositiveIntegerField()
    included_meals = models.JSONField(default=list)  # e.g. ["lunch", "dinner"]
    duration_days = models.PositiveIntegerField(default=30)  # Default subscription duration
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom duration constraint fields
    min_duration_days = models.PositiveIntegerField(default=7)
    max_duration_days = models.PositiveIntegerField(default=90)
    allow_custom_duration = models.BooleanField(default=True)
    daily_rate_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional: Override calculated daily rate"
    )

    def get_daily_rate(self) -> Decimal:
        """Get daily rate (override or calculated from base_price)"""
        if self.daily_rate_override:
            return self.daily_rate_override
        return Decimal(self.base_price) / Decimal(self.duration_days)
    
    def validate_duration(self, days: int) -> bool:
        """Check if duration is within allowed range"""
        if not self.allow_custom_duration:
            return days == self.duration_days
        return self.min_duration_days <= days <= self.max_duration_days
    
    def calculate_price_for_duration(self, days: int) -> int:
        """Calculate price for a given duration"""
        return int(round(self.get_daily_rate() * days))

    def __str__(self):
        return f"{self.name} ({self.service_type})"

    class Meta:
        ordering = ['service_type', 'base_price']


class Cart(models.Model):
    """User's shopping cart for meal plans"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_total(self) -> int:
        """Calculate total price of all items in cart"""
        return sum(item.calculated_price for item in self.items.all())
    
    def get_item_count(self) -> int:
        """Get number of items in cart"""
        return self.items.count()
    
    def clear(self) -> None:
        """Remove all items from cart"""
        self.items.all().delete()
    
    def __str__(self):
        return f"Cart for {self.user.username} ({self.get_item_count()} items)"


class CartItem(models.Model):
    """Individual plan in user's cart with custom duration"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    custom_duration_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'plan']  # One plan per cart
    
    @property
    def daily_rate(self) -> Decimal:
        """Calculate daily rate from plan's base price"""
        return self.plan.get_daily_rate()
    
    @property
    def calculated_price(self) -> int:
        """Calculate price based on custom duration"""
        return int(round(self.daily_rate * self.custom_duration_days))
    
    def __str__(self):
        return f"{self.plan.name} ({self.custom_duration_days} days) - ₹{self.calculated_price}"


class BundleOrder(models.Model):
    """Groups multiple subscriptions from a single checkout"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('PARTIALLY_CANCELLED', 'Partially Cancelled'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bundle_orders'
    )
    total_amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def get_subscription_count(self) -> int:
        """Get number of subscriptions in this bundle"""
        return self.subscriptions.count()
    
    def update_status(self) -> None:
        """Update status based on subscription statuses"""
        subscriptions = self.subscriptions.all()
        if not subscriptions.exists():
            return
            
        cancelled_count = subscriptions.filter(status='CANCELLED').count()
        total_count = subscriptions.count()
        
        if cancelled_count == 0:
            self.status = 'PAID'
        elif cancelled_count == total_count:
            self.status = 'CANCELLED'
        else:
            self.status = 'PARTIALLY_CANCELLED'
        self.save()
    
    def __str__(self):
        return f"Bundle #{self.id} - {self.user.username} - ₹{self.total_amount}"
    
    class Meta:
        ordering = ['-created_at']

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('RENEWED','Renewed')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    bundle_order = models.ForeignKey(
        BundleOrder, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subscriptions'
    )
    base_price = models.PositiveIntegerField()
    total_paid = models.PositiveIntegerField()
    pending_payment_amount = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Amount currently pending payment (for renewals)"
    )
    start_date = models.DateField()
    base_end_date = models.DateField()  # start_date + duration days
    adjusted_end_date = models.DateField()  # base_end_date + leave days
    leave_days = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    payment_gateway = models.CharField(max_length=30, blank=True)
    payment_transaction_id = models.CharField(max_length=100, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount_calculated = models.PositiveIntegerField(default=0)
    refund_status = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now().date()
        if not self.base_end_date:
            self.base_end_date = self.start_date + timedelta(days=self.plan.duration_days)
        if not self.adjusted_end_date:
            self.adjusted_end_date = self.base_end_date
        today = timezone.now().date()
        # Make sure you have an 'adjusted_end_date' field
        if self.adjusted_end_date and self.adjusted_end_date <= today:
            self.status = 'EXPIRED'
        elif hasattr(self, 'days_remaining') and self.days_remaining == 0:
            self.status = 'EXPIRED' 

        if self.adjusted_end_date:
            if self.adjusted_end_date <= today:
                # Subscription has expired
                if self.status not in ['CANCELLED', 'REFUNDED']:
                    self.status = 'EXPIRED'
            elif self.adjusted_end_date > today:
                # Subscription is current/future
                if self.status == 'EXPIRED':
                    # Reactivate if date was extended
                    self.status = 'ACTIVE'
                elif self.status == 'PENDING_PAYMENT':
                    # Keep pending until payment is confirmed
                    pass            
        # You might also want to check

        super().save(*args, **kwargs)

    def calculate_refund(self):
        """Calculate refund amount for cancellation"""
        if self.status != 'ACTIVE':
            return 0
        
        today = timezone.now().date()
        if today >= self.adjusted_end_date:
            return 0
        
        remaining_days = (self.adjusted_end_date - today).days
        total_days = (self.adjusted_end_date - self.start_date).days
        
        if remaining_days <= 0:
            return 0
        
        # Tiered refund system
        if remaining_days >= total_days * 0.75:  # 75% or more remaining
            refund_percentage = 0.90
        elif remaining_days >= total_days * 0.50:  # 50-75% remaining
            refund_percentage = 0.75
        elif remaining_days >= total_days * 0.25:  # 25-50% remaining
            refund_percentage = 0.50
        else:  # Less than 25% remaining
            refund_percentage = 0.25
        
        return int(self.total_paid * refund_percentage)

    def extend_subscription(self, days):
        """Extend subscription by given number of days"""
        self.adjusted_end_date += timedelta(days=days)
        self.leave_days += days
        self.save()

    def __str__(self):
        return f"{self.user.username} | {self.plan.code} ({self.start_date})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['adjusted_end_date']),
        ]

class Leave(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('AUTO_APPROVED', 'Auto Approved'),  # For very short leaves if needed
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='leaves')
    leave_start_date = models.DateField()
    leave_end_date = models.DateField()
    duration_days = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Admin workflow fields
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_leaves'
    )
    admin_comment = models.TextField(blank=True)
    
    # Extension tracking
    extension_applied = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.duration_days:
            self.duration_days = (self.leave_end_date - self.leave_start_date).days + 1
        
        # Remove auto-approval logic - everything goes to PENDING
        if not self.pk:  # Only for new requests
            self.status = 'PENDING'
        
        super().save(*args, **kwargs)
    
    def approve_leave(self, admin_user, comment=""):
        """Approve leave request and extend subscription"""
        self.status = 'APPROVED'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.admin_comment = comment
        self.save()
        
        # Extend subscription only after approval
        if not self.extension_applied:
            self.subscription.extend_subscription(self.duration_days)
            self.extension_applied = True
            self.save()
    
    def reject_leave(self, admin_user, comment=""):
        """Reject leave request"""
        self.status = 'REJECTED'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.admin_comment = comment
        self.save()

    def __str__(self):
        return f"{self.subscription} | {self.leave_start_date} to {self.leave_end_date} ({self.duration_days}d) - {self.status}"

    class Meta:
        ordering = ['-requested_at']
