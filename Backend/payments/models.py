from django.db import models
from django.conf import settings
from django.utils import timezone

class Payment(models.Model):
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payments'
    )
    payment_gateway = models.CharField(max_length=30, default='razorpay')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.PositiveIntegerField()  # Amount in paise
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=200, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['gateway_order_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_gateway']),
            models.Index(fields=['amount']),
        ]

    def __str__(self):
        return f"{self.user.username} | {self.amount/100} INR | {self.status}"

class RazorpayOrder(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    signature = models.CharField(max_length=200, null=True, blank=True)
    amount = models.IntegerField()  # in paise
    currency = models.CharField(max_length=3, default='INR')
    subscription = models.ForeignKey(
        'subscriptions.Subscription', 
        on_delete=models.CASCADE,
        related_name='razorpay_orders'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='razorpay_orders'
    )
    status = models.CharField(max_length=20, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    receipt = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.order_id} | {self.amount/100} INR | {self.status}"

class RefundRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSED', 'Processed'),
        ('PAID', 'Paid (Manual)'),
    ]
    
    subscription = models.OneToOneField(
        'subscriptions.Subscription', 
        on_delete=models.CASCADE,
        related_name='refund_request'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='refund_requests'
    )
    original_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_requests'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_comment = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    refund_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_refund_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requested_by', 'status']),
        ]

    def __str__(self):
        return f"Refund: {self.subscription} | {self.amount} INR | {self.status}"
