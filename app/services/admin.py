from django.contrib import admin
from .models import Service
from shops.models import Shop

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_name', 'created_at', 'prices_count')
    list_filter = ('shop', 'created_at')
    search_fields = ('name', 'shop__name', 'shop__owner__username')
    readonly_fields = ('created_at', 'prices_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Service Information', {
            'fields': ('shop', 'name')
        }),
        ('Metadata', {
            'fields': ('created_at', 'prices_count'),
            'classes': ('collapse',)
        })
    )
    
    def shop_name(self, obj):
        return obj.shop.name
    shop_name.short_description = 'Shop'
    shop_name.admin_order_field = 'shop__name'
    
    def prices_count(self, obj):
        return obj.prices.count()
    prices_count.short_description = 'Price Entries'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see services for their shop
            if hasattr(request.user, 'shop'):
                return qs.filter(shop=request.user.shop)
            return qs.none()
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shop" and not request.user.is_superuser:
            if hasattr(request.user, 'shop'):
                kwargs["queryset"] = Shop.objects.filter(id=request.user.shop.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
