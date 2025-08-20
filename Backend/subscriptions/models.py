from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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
    can_add_breakfast = models.BooleanField(default=True)
    breakfast_addon_price = models.PositiveIntegerField(default=600)
    duration_days = models.PositiveIntegerField(default=30)  # Subscription duration
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.service_type})"

    class Meta:
        ordering = ['service_type', 'base_price']

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
    breakfast_included = models.BooleanField(default=False)
    base_price = models.PositiveIntegerField()
    breakfast_addon_price = models.PositiveIntegerField(default=0)
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
        if self.adjusted_end_date and self.adjusted_end_date < today:
            self.status = 'EXPIRED'
        elif hasattr(self, 'days_remaining') and self.days_remaining == 0:
            self.status = 'EXPIRED' 

        if self.adjusted_end_date:
            if self.adjusted_end_date < today:
                # Subscription has expired
                if self.status not in ['CANCELLED', 'REFUNDED']:
                    self.status = 'EXPIRED'
            elif self.adjusted_end_date >= today:
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
