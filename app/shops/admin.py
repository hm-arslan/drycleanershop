from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Shop, ShopStaff


class ShopStaffInline(admin.TabularInline):
    model = ShopStaff
    extra = 0
    readonly_fields = ('hire_date', 'created_at', 'permissions_summary')
    fields = (
        'user', 'position', 'is_active', 'permissions_summary',
        'can_take_orders', 'can_update_orders', 'can_register_customers', 'hourly_rate'
    )
    
    def permissions_summary(self, obj):
        if obj and obj.pk:
            permissions = obj.get_permissions()
            if permissions:
                return ', '.join(permissions)
            return 'No permissions'
        return '-'
    permissions_summary.short_description = 'Current Permissions'

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_info', 'phone', 'created_at', 'services_count', 'items_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__username', 'owner__email', 'phone', 'address')
    readonly_fields = ('created_at', 'services_count', 'items_count', 'orders_count')
    ordering = ('-created_at',)
    inlines = [ShopStaffInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'phone')
        }),
        ('Address', {
            'fields': ('address',)
        }),
        ('Statistics', {
            'fields': ('services_count', 'items_count', 'orders_count', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def owner_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/>{}', 
            obj.owner.username,
            obj.owner.email
        )
    owner_info.short_description = 'Owner'
    
    def services_count(self, obj):
        return obj.services.count()
    services_count.short_description = 'Services'
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'
    
    def orders_count(self, obj):
        return obj.orders.count() if hasattr(obj, 'orders') else 0
    orders_count.short_description = 'Orders'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see their own shop
            if hasattr(request.user, 'shop'):
                return qs.filter(id=request.user.shop.id)
            return qs.none()
        return qs


@admin.register(ShopStaff)
class ShopStaffAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'shop_link', 'position', 'permissions_display', 'is_active', 'hire_date')
    list_filter = ('is_active', 'position', 'hire_date', 'can_take_orders', 'can_update_orders', 'can_register_customers')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'shop__name', 'position')
    ordering = ('-hire_date',)
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('user', 'shop', 'position', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_take_orders', 'can_update_orders', 'can_register_customers')
        }),
        ('Employment Details', {
            'fields': ('hourly_rate', 'hire_date', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('hire_date', 'created_at')
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = 'User'
    
    def shop_link(self, obj):
        url = reverse('admin:shops_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)
    shop_link.short_description = 'Shop'
    
    def permissions_display(self, obj):
        permissions = obj.get_permissions()
        badges = []
        colors = {
            'Take Orders': '#28a745',
            'Update Orders': '#007bff', 
            'Register Customers': '#ffc107'
        }
        
        for perm in permissions:
            color = colors.get(perm, '#6c757d')
            badges.append(f'<span style="background-color: {color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 3px;">{perm}</span>')
        
        return format_html(''.join(badges)) if badges else format_html('<span style="color: #dc3545;">No permissions</span>')
    permissions_display.short_description = 'Permissions'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see staff from their shop
            if hasattr(request.user, 'shop'):
                return qs.filter(shop=request.user.shop)
            return qs.none()
        return qs
