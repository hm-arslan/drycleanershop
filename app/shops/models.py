from django.db import models
from django.conf import settings
from core.validators import validate_phone_number, validate_no_special_chars, validate_text_length, validate_safe_string

User = settings.AUTH_USER_MODEL

class Shop(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shop")  
    name = models.CharField(
        max_length=255,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="Shop name (alphanumeric characters, spaces, hyphens, periods only)"
    )
    address = models.TextField(
        validators=[validate_safe_string],
        help_text="Shop address"
    )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone_number],
        help_text="Contact phone number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Shop is currently active")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        super().clean()
        if self.name:
            validate_text_length(self.name, max_length=255)
        if self.address:
            validate_text_length(self.address, max_length=1000)

    def __str__(self):
        return self.name


class ShopStaff(models.Model):
    """Staff members working at a shop"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='staff_members')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    position = models.CharField(
        max_length=100,
        validators=[validate_safe_string],
        help_text="Job position/title"
    )
    is_active = models.BooleanField(default=True, help_text="Staff member is currently active")
    can_take_orders = models.BooleanField(default=True, help_text="Can create and manage orders")
    can_update_orders = models.BooleanField(default=True, help_text="Can update order status")
    can_register_customers = models.BooleanField(default=True, help_text="Can register new customers")
    hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Hourly wage rate"
    )
    hire_date = models.DateField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        validators=[validate_safe_string],
        help_text="Additional notes about the staff member"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['user']),
        ]
        verbose_name = "Shop Staff Member"
        verbose_name_plural = "Shop Staff Members"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.shop.name}"
    
    def get_permissions(self):
        """Get staff member permissions"""
        return {
            'can_take_orders': self.can_take_orders,
            'can_update_orders': self.can_update_orders,
            'can_register_customers': self.can_register_customers,
        }