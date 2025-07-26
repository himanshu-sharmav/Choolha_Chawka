from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('food_complaint', 'Food Complaint'),
        ('general_feedback', 'General Feedback'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
    ]
    
    # User and identification
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='feedbacks'
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    
    # Feedback content
    subject = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="1=Very Poor, 5=Excellent"
    )
    
    # Context (for food complaints)
    subscription = models.ForeignKey(
        'subscriptions.Subscription', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='feedbacks'
    )
    meal_date = models.DateField(null=True, blank=True)
    meal_type = models.CharField(
        max_length=20, 
        choices=MEAL_TYPES,
        null=True, blank=True
    )
    
    # Management
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin response
    admin_response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='feedback_responses'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback_type', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.subject} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Auto-set priority based on feedback type
        if not self.priority or self.priority == 'medium':
            if self.feedback_type == 'food_complaint':
                self.priority = 'high'
            elif self.feedback_type == 'general_feedback':
                self.priority = 'medium'
        super().save(*args, **kwargs)
    
    @property
    def is_food_complaint(self):
        return self.feedback_type == 'food_complaint'
    
    @property
    def is_urgent(self):
        return self.priority in ['high', 'urgent']
    
    @property
    def days_since_created(self):
        return (timezone.now().date() - self.created_at.date()).days

class FeedbackAttachment(models.Model):
    feedback = models.ForeignKey(
        Feedback, 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.ImageField(upload_to='feedback_attachments/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['feedback']),
        ]
    
    def __str__(self):
        return f"Attachment for {self.feedback.subject}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
