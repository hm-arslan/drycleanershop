from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.validators import (
    validate_safe_string, validate_no_special_chars, 
    validate_text_length, validate_phone_number
)

User = settings.AUTH_USER_MODEL


class CustomerProfile(models.Model):
    PICKUP_TYPE_CHOICES = (
        ('drop_off', 'Drop Off'),
        ('pickup', 'Pickup Service'),
    )
    
    COMMUNICATION_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Phone Call'),
        ('app', 'App Notification'),
    )
    
    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True, help_text="Customer's date of birth")
    preferred_name = models.CharField(
        max_length=50, 
        blank=True,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="How the customer prefers to be addressed"
    )
    emergency_contact_name = models.CharField(
        max_length=100, 
        blank=True,
        validators=[validate_safe_string],
        help_text="Emergency contact person"
    )
    emergency_contact_phone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[validate_phone_number],
        help_text="Emergency contact phone number"
    )
    
    # Customer Preferences
    preferred_pickup_type = models.CharField(
        max_length=20, 
        choices=PICKUP_TYPE_CHOICES, 
        default='drop_off',
        help_text="Default pickup preference"
    )
    preferred_communication = models.CharField(
        max_length=20, 
        choices=COMMUNICATION_CHOICES, 
        default='email',
        help_text="Preferred communication method"
    )
    special_instructions = models.TextField(
        blank=True,
        validators=[validate_safe_string],
        help_text="Special handling instructions or notes"
    )
    
    # Loyalty & Points
    loyalty_points = models.IntegerField(
        default=0,
        help_text="Current loyalty points balance"
    )
    membership_tier = models.CharField(
        max_length=20, 
        choices=TIER_CHOICES, 
        default='bronze',
        help_text="Current membership tier"
    )
    total_spent = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Total amount spent by customer"
    )
    
    # Analytics
    first_order_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date of first order"
    )
    last_order_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date of most recent order"
    )
    total_orders = models.IntegerField(
        default=0,
        help_text="Total number of orders placed"
    )
    average_order_value = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text="Average order value"
    )
    
    # Marketing Preferences
    email_marketing = models.BooleanField(
        default=True,
        help_text="Receive marketing emails"
    )
    sms_marketing = models.BooleanField(
        default=False,
        help_text="Receive marketing SMS"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['membership_tier']),
            models.Index(fields=['total_spent']),
            models.Index(fields=['loyalty_points']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        super().clean()
        if self.preferred_name:
            validate_text_length(self.preferred_name, max_length=50)
        if self.special_instructions:
            validate_text_length(self.special_instructions, max_length=1000)
    
    def update_membership_tier(self):
        """Update membership tier based on total spent"""
        if self.total_spent >= 1000:
            self.membership_tier = 'platinum'
        elif self.total_spent >= 500:
            self.membership_tier = 'gold'
        elif self.total_spent >= 200:
            self.membership_tier = 'silver'
        else:
            self.membership_tier = 'bronze'
        self.save(update_fields=['membership_tier'])
    
    def add_loyalty_points(self, points, description="Points earned"):
        """Add loyalty points and create transaction record"""
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points'])
        
        # Create loyalty transaction record
        LoyaltyTransaction.objects.create(
            customer=self.user,
            type='earned',
            points=points,
            description=description
        )
    
    def redeem_loyalty_points(self, points, description="Points redeemed"):
        """Redeem loyalty points if sufficient balance"""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points'])
            
            # Create loyalty transaction record
            LoyaltyTransaction.objects.create(
                customer=self.user,
                type='redeemed',
                points=-points,
                description=description
            )
            return True
        return False
    
    def __str__(self):
        display_name = self.preferred_name or self.user.get_full_name() or self.user.username
        return f"{display_name} ({self.membership_tier.title()})"


class CustomerAddress(models.Model):
    ADDRESS_TYPES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    
    # Address Type & Label
    type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    label = models.CharField(
        max_length=50,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="Address label (e.g., 'Main Office', 'Home')"
    )
    
    # Address Details
    street_address = models.CharField(
        max_length=255,
        validators=[validate_safe_string],
        help_text="Street address"
    )
    apartment_unit = models.CharField(
        max_length=50, 
        blank=True,
        validators=[validate_safe_string],
        help_text="Apartment, suite, or unit number"
    )
    city = models.CharField(
        max_length=100,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="City"
    )
    state = models.CharField(
        max_length=50,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="State or province"
    )
    postal_code = models.CharField(
        max_length=20,
        validators=[validate_safe_string],
        help_text="ZIP or postal code"
    )
    country = models.CharField(
        max_length=100, 
        default='USA',
        validators=[validate_safe_string, validate_no_special_chars]
    )
    
    # Preferences
    is_default = models.BooleanField(
        default=False,
        help_text="Use as default address"
    )
    pickup_instructions = models.TextField(
        blank=True,
        validators=[validate_safe_string],
        help_text="Special pickup/delivery instructions"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-is_default', 'label']
        indexes = [
            models.Index(fields=['customer', 'is_default']),
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['customer', 'label']  # Prevent duplicate labels per customer
    
    def clean(self):
        super().clean()
        # Validate text lengths
        for field, max_length in [
            ('label', 50), ('street_address', 255), ('apartment_unit', 50),
            ('city', 100), ('state', 50), ('pickup_instructions', 500)
        ]:
            value = getattr(self, field)
            if value:
                validate_text_length(value, max_length=max_length)
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per customer
        if self.is_default:
            CustomerAddress.objects.filter(
                customer=self.customer, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [self.street_address]
        if self.apartment_unit:
            address_parts.append(f"#{self.apartment_unit}")
        address_parts.append(f"{self.city}, {self.state} {self.postal_code}")
        if self.country != 'USA':
            address_parts.append(self.country)
        return ", ".join(address_parts)
    
    def __str__(self):
        return f"{self.label}: {self.full_address}"


class LoyaltyTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('bonus', 'Bonus Points'),
        ('adjustment', 'Manual Adjustment'),
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loyalty_transactions")
    
    # Transaction Details
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField(help_text="Points amount (positive for earned, negative for redeemed)")
    description = models.CharField(
        max_length=200,
        validators=[validate_safe_string],
        help_text="Description of the transaction"
    )
    
    # References
    order = models.ForeignKey(
        'orders.Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="loyalty_transactions"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When these points expire (if applicable)"
    )
    
    # Staff who processed (for manual adjustments)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="processed_loyalty_transactions"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def clean(self):
        super().clean()
        if self.description:
            validate_text_length(self.description, max_length=200)
    
    def __str__(self):
        sign = "+" if self.points >= 0 else ""
        return f"{self.customer.username}: {sign}{self.points} pts - {self.description}"
