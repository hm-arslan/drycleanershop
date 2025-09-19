from django.contrib.auth.models import AbstractUser
from django.db import models
from core.validators import validate_phone_number, validate_no_special_chars

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('shop_owner', 'Shop Owner'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(
        max_length=20, 
        unique=True,
        validators=[validate_phone_number],
        help_text="Enter a valid phone number"
    )
    
    # Add security fields
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.username:
            validate_no_special_chars(self.username)

    def __str__(self):
        return f"{self.username} ({self.role})"
