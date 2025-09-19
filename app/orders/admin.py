from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    
class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('changed_at', 'changed_by')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'shop_name', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'pickup_type', 'shop', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer__username')
    readonly_fields = ('order_number', 'subtotal', 'total_amount', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'pickup_type')
        }),
        ('Customer Details', {
            'fields': ('customer', 'customer_name', 'customer_phone', 'pickup_address')
        }),
        ('Shop Information', {
            'fields': ('shop',)
        }),
        ('Order Details', {
            'fields': ('special_instructions', 'estimated_completion')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def shop_name(self, obj):
        return obj.shop.name
    shop_name.short_description = 'Shop'
    shop_name.admin_order_field = 'shop__name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if hasattr(request.user, 'shop'):
                return qs.filter(shop=request.user.shop)
            return qs.filter(customer=request.user)
        return qs

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'service_item_combo', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__shop', 'service_price__service', 'service_price__item')
    search_fields = ('order__order_number', 'service_price__service__name', 'service_price__item__name')
    readonly_fields = ('total_price',)
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    order_number.admin_order_field = 'order__order_number'
    
    def service_item_combo(self, obj):
        return f"{obj.service_price.service.name} + {obj.service_price.item.name}"
    service_item_combo.short_description = 'Service + Item'

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'status', 'changed_by', 'changed_at')
    list_filter = ('status', 'changed_at')
    search_fields = ('order__order_number', 'changed_by__username')
    readonly_fields = ('changed_at',)
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order #'
    order_number.admin_order_field = 'order__order_number'
