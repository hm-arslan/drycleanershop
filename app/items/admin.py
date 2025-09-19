from django.contrib import admin
from django.utils.html import format_html
from .models import Item, ServicePrice
from shops.models import Shop
from services.models import Service

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_name', 'created_at', 'prices_count')
    list_filter = ('shop', 'created_at')
    search_fields = ('name', 'shop__name', 'shop__owner__username')
    readonly_fields = ('created_at', 'prices_count')
    ordering = ('-created_at',)
    
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
            if hasattr(request.user, 'shop'):
                return qs.filter(shop=request.user.shop)
            return qs.none()
        return qs

@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    list_display = ('service_item_combo', 'shop_name', 'price', 'formatted_price')
    list_filter = ('shop', 'service', 'item')
    search_fields = ('service__name', 'item__name', 'shop__name')
    ordering = ('shop', 'service', 'item')
    
    fieldsets = (
        ('Pricing Information', {
            'fields': ('shop', 'service', 'item', 'price')
        }),
    )
    
    def service_item_combo(self, obj):
        return f"{obj.service.name} + {obj.item.name}"
    service_item_combo.short_description = 'Service + Item'
    
    def shop_name(self, obj):
        return obj.shop.name
    shop_name.short_description = 'Shop'
    shop_name.admin_order_field = 'shop__name'
    
    def formatted_price(self, obj):
        return format_html('<strong>${}</strong>', obj.price)
    formatted_price.short_description = 'Price'
    formatted_price.admin_order_field = 'price'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'shop'):
                return qs.filter(shop=request.user.shop)
            return qs.none()
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and hasattr(request.user, 'shop'):
            if db_field.name == "shop":
                kwargs["queryset"] = Shop.objects.filter(id=request.user.shop.id)
            elif db_field.name == "service":
                kwargs["queryset"] = Service.objects.filter(shop=request.user.shop)
            elif db_field.name == "item":
                kwargs["queryset"] = Item.objects.filter(shop=request.user.shop)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
