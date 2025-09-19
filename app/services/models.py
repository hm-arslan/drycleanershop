from django.db import models
from shops.models import Shop
from core.validators import validate_safe_string, validate_no_special_chars, validate_text_length

class Service(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(
        max_length=100,
        validators=[validate_safe_string, validate_no_special_chars],
        help_text="Service name (e.g., 'Dry Clean', 'Wash & Fold')"
    )
    description = models.TextField(
        blank=True,
        validators=[validate_safe_string],
        help_text="Optional service description"
    )
    is_active = models.BooleanField(default=True, help_text="Service is currently offered")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("shop", "name")  # no duplicate service names per shop
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
