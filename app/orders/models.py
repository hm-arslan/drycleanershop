from django.db import models
from django.conf import settings
from decimal import Decimal
from shops.models import Shop
from items.models import ServicePrice

User = settings.AUTH_USER_MODEL

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PICKUP_TYPE_CHOICES = (
        ('drop_off', 'Drop Off'),
        ('pickup', 'Pickup Service'),
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pickup_type = models.CharField(max_length=20, choices=PICKUP_TYPE_CHOICES, default='drop_off')
    
    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    pickup_address = models.TextField(blank=True, null=True)  # For pickup service
    
    # Order details
    special_instructions = models.TextField(blank=True, null=True)
    estimated_completion = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: SHOP_ID + timestamp with microseconds for uniqueness
            import time
            import random
            timestamp = str(int(time.time() * 1000000))[-10:]  # Last 10 digits of microsecond timestamp
            random_suffix = random.randint(10, 99)  # Add random suffix for extra uniqueness
            self.order_number = f"{self.shop.id}{timestamp}{random_suffix}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate order total from order items"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = self.subtotal
        self.save()
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    service_price = models.ForeignKey(ServicePrice, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)  # Item-specific notes
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.service_price.price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order total when item is saved
        self.order.calculate_total()
    
    def __str__(self):
        return f"{self.service_price.service.name} + {self.service_price.item.name} x{self.quantity}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Order #{self.order.order_number} -> {self.status}"
