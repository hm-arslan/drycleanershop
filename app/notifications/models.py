from django.db import models
from django.conf import settings
from django.utils import timezone
from core.validators import validate_safe_string


class NotificationTemplate(models.Model):
    """Template for creating standardized notifications"""
    TYPE_CHOICES = [
        ('order_status', 'Order Status Update'),
        ('loyalty_points', 'Loyalty Points'),
        ('promotion', 'Promotion'),
        ('reminder', 'Reminder'),
        ('system', 'System Notification'),
        ('welcome', 'Welcome Message'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    name = models.CharField(max_length=100, unique=True, validators=[validate_safe_string])
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title_template = models.CharField(max_length=200, validators=[validate_safe_string])
    message_template = models.TextField(validators=[validate_safe_string])
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['type', 'name']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Notification(models.Model):
    """In-app notifications for users"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    title = models.CharField(max_length=200, validators=[validate_safe_string])
    message = models.TextField(validators=[validate_safe_string])
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    
    # Optional references to related objects
    order = models.ForeignKey(
        'orders.Order', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='notifications'
    )
    shop = models.ForeignKey(
        'shops.Shop', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='notifications'
    )
    
    # Template reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='notifications'
    )
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_archived(self):
        """Archive notification"""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def age_in_hours(self):
        """Get age of notification in hours"""
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Notification type preferences
    order_notifications = models.BooleanField(default=True)
    loyalty_notifications = models.BooleanField(default=True)
    promotion_notifications = models.BooleanField(default=True)
    reminder_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    
    # Frequency settings
    daily_digest = models.BooleanField(default=False)
    immediate_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class NotificationBatch(models.Model):
    """Track batch notification sending for analytics"""
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, validators=[validate_safe_string])
    message = models.TextField(validators=[validate_safe_string])
    
    # Targeting
    target_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notification_batches')
    target_shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, blank=True, null=True)
    
    # Status
    is_sent = models.BooleanField(default=False)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_notification_batches'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_sent']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Batch: {self.title} ({self.sent_count} sent)"
