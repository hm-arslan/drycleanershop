from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomerProfile, CustomerAddress, LoyaltyTransaction

# Remove inlines since they have ForeignKey to User, not CustomerProfile
# Instead, we'll show links to related data

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'user_info', 'membership_tier', 'loyalty_points', 
        'total_spent', 'total_orders', 'last_order_date', 'is_active'
    )
    list_filter = (
        'membership_tier', 'preferred_communication', 'preferred_pickup_type',
        'email_marketing', 'sms_marketing', 'is_active', 'created_at'
    )
    search_fields = (
        'user__username', 'user__email', 'user__phone', 
        'preferred_name', 'user__first_name', 'user__last_name'
    )
    readonly_fields = (
        'loyalty_points', 'membership_tier', 'total_spent', 'total_orders',
        'average_order_value', 'first_order_date', 'last_order_date',
        'created_at', 'updated_at', 'user_orders_link'
    )
    ordering = ['-total_spent', '-loyalty_points']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'preferred_name', 'date_of_birth', 'user_orders_link')
        }),
        ('Contact & Emergency', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Preferences', {
            'fields': (
                'preferred_pickup_type', 'preferred_communication', 
                'special_instructions', 'email_marketing', 'sms_marketing'
            )
        }),
        ('Loyalty & Analytics', {
            'fields': (
                'loyalty_points', 'membership_tier', 'total_spent', 'total_orders',
                'average_order_value', 'first_order_date', 'last_order_date'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def display_name(self, obj):
        return obj.preferred_name or obj.user.get_full_name() or obj.user.username
    display_name.short_description = 'Display Name'
    display_name.admin_order_field = 'preferred_name'
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/>📧 {}<br/>📱 {}',
            obj.user.username,
            obj.user.email,
            obj.user.phone
        )
    user_info.short_description = 'User Details'
    
    def user_orders_link(self, obj):
        if obj.user.orders.exists():
            url = reverse('admin:orders_order_changelist') + f'?customer__id__exact={obj.user.id}'
            count = obj.user.orders.count()
            return format_html('<a href="{}" target="_blank">View {} Orders</a>', url, count)
        return 'No orders'
    user_orders_link.short_description = 'Orders'


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'label', 'type', 'city', 'state', 'is_default', 'is_active')
    list_filter = ('type', 'is_default', 'is_active', 'state', 'country', 'created_at')
    search_fields = (
        'customer__username', 'customer__email', 'label',
        'street_address', 'city', 'state', 'postal_code'
    )
    readonly_fields = ('created_at', 'updated_at', 'full_address')
    ordering = ['customer__username', '-is_default', 'label']
    
    fieldsets = (
        ('Customer & Label', {
            'fields': ('customer', 'type', 'label', 'is_default')
        }),
        ('Address Details', {
            'fields': (
                'street_address', 'apartment_unit', 'city', 
                'state', 'postal_code', 'country', 'full_address'
            )
        }),
        ('Preferences', {
            'fields': ('pickup_instructions',)
        }),
        ('Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def customer_name(self, obj):
        profile = getattr(obj.customer, 'customer_profile', None)
        if profile and profile.preferred_name:
            return f"{profile.preferred_name} ({obj.customer.username})"
        return obj.customer.username
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__username'


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name', 'type', 'points_display', 'description', 
        'order_link', 'created_at', 'expires_at'
    )
    list_filter = ('type', 'created_at', 'expires_at')
    search_fields = (
        'customer__username', 'customer__email', 'description',
        'order__order_number'
    )
    readonly_fields = ('created_at', 'customer_profile_link')
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('customer', 'customer_profile_link', 'type', 'points', 'description')
        }),
        ('References', {
            'fields': ('order', 'processed_by')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at')
        })
    )
    
    def customer_name(self, obj):
        profile = getattr(obj.customer, 'customer_profile', None)
        if profile and profile.preferred_name:
            return f"{profile.preferred_name} ({obj.customer.username})"
        return obj.customer.username
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__username'
    
    def points_display(self, obj):
        color = 'green' if obj.points > 0 else 'red'
        sign = '+' if obj.points > 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.points
        )
    points_display.short_description = 'Points'
    points_display.admin_order_field = 'points'
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Order'
    
    def customer_profile_link(self, obj):
        if hasattr(obj.customer, 'customer_profile'):
            url = reverse('admin:customers_customerprofile_change', args=[obj.customer.customer_profile.id])
            return format_html('<a href="{}" target="_blank">View Profile</a>', url)
        return 'No profile'
    customer_profile_link.short_description = 'Profile'


# Customize admin site header
admin.site.site_header = 'Dry Cleaner Shop Administration'
admin.site.site_title = 'Dry Cleaner Admin'
admin.site.index_title = 'Welcome to Dry Cleaner Shop Admin'
