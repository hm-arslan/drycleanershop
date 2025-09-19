from django.db import models
from django.core.exceptions import ValidationError
from shops.models import Shop
from services.models import Service
from core.validators import validate_safe_string, validate_no_special_chars, validate_text_length, validate_price

class Item(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(
        max_length=100,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="Item name (e.g., 'Shirt', 'Dress', 'Suit')"
    )
    description = models.TextField(
        blank=True,
        validators=[validate_safe_string],
        help_text="Optional item description"
    )
    is_active = models.BooleanField(default=True, help_text="Item is currently accepted")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("shop", "name")  # no duplicate item names per shop
        ordering = ['name']
        indexes = [
            models.Index(fields=['shop', 'name']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        super().clean()
        if self.name:
            validate_text_length(self.name, max_length=100)
        if self.description:
            validate_text_length(self.description, max_length=500)

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class ServicePrice(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="service_prices")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="prices")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="prices")
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[validate_price],
        help_text="Price for this service-item combination"
    )
    is_active = models.BooleanField(default=True, help_text="Price is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("shop", "service", "item")  # avoid duplicates
        ordering = ['service__name', 'item__name']
        indexes = [
            models.Index(fields=['shop', 'service', 'item']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
        ]
    
    def clean(self):
        super().clean()
        # Ensure service and item belong to the same shop
        if self.service and self.service.shop != self.shop:
            raise ValidationError("Service must belong to the same shop")
        if self.item and self.item.shop != self.shop:
            raise ValidationError("Item must belong to the same shop")

    def __str__(self):
        return f"{self.service.name} + {self.item.name} = ${self.price}"
