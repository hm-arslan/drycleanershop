from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import NotificationTemplate, Notification, NotificationPreference, NotificationBatch


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ('created_at', 'read_at', 'age_in_hours')
    fields = ('title', 'priority', 'status', 'created_at', 'read_at', 'expires_at')
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'order', 'shop')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type', 'priority', 'is_active', 
        'notification_count', 'created_at'
    )
    list_filter = ('type', 'priority', 'is_active', 'created_at')
    search_fields = ('name', 'title_template', 'message_template')
    readonly_fields = ('created_at', 'updated_at', 'notification_count')
    ordering = ['type', 'name']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'type', 'priority', 'is_active')
        }),
        ('Template Content', {
            'fields': ('title_template', 'message_template')
        }),
        ('Usage Statistics', {
            'fields': ('notification_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def notification_count(self, obj):
        count = obj.notifications.count()
        if count > 0:
            url = reverse('admin:notifications_notification_changelist') + f'?template__id__exact={obj.id}'
            return format_html('<a href=\"{}\" target=\"_blank\">{} notifications</a>', url, count)
        return '0 notifications'
    notification_count.short_description = 'Usage Count'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_name', 'title_truncated', 'template_type', 
        'priority_badge', 'status_badge', 'age_display', 'created_at'
    )
    list_filter = (
        'status', 'priority', 'template__type', 'created_at', 
        'expires_at', 'template'
    )
    search_fields = (
        'recipient__username', 'recipient__email', 'title', 'message',
        'order__order_number', 'shop__name'
    )
    readonly_fields = (
        'created_at', 'read_at', 'age_in_hours', 'is_expired',
        'recipient_profile_link', 'order_link', 'shop_link'
    )
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'recipient_profile_link', 'title', 'message', 'priority')
        }),
        ('Status & Timing', {
            'fields': ('status', 'created_at', 'read_at', 'expires_at', 'age_in_hours', 'is_expired')
        }),
        ('References', {
            'fields': ('template', 'order', 'order_link', 'shop', 'shop_link')
        }),
        ('Additional Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipient', 'template', 'order', 'shop'
        ).prefetch_related('recipient__customer_profile')
    
    def recipient_name(self, obj):
        profile = getattr(obj.recipient, 'customer_profile', None)
        if profile and profile.preferred_name:
            return f"{profile.preferred_name} ({obj.recipient.username})"
        return obj.recipient.get_full_name() or obj.recipient.username
    recipient_name.short_description = 'Recipient'
    recipient_name.admin_order_field = 'recipient__username'
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Title'
    title_truncated.admin_order_field = 'title'
    
    def template_type(self, obj):
        if obj.template:
            return obj.template.get_type_display()
        return '-'
    template_type.short_description = 'Type'
    template_type.admin_order_field = 'template__type'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'gray',
            'normal': 'blue',
            'high': 'orange',
            'urgent': 'red'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def status_badge(self, obj):
        colors = {
            'unread': 'red',
            'read': 'green',
            'archived': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def age_display(self, obj):
        hours = obj.age_in_hours
        if hours < 1:
            return f"{int(hours * 60)}m"
        elif hours < 24:
            return f"{int(hours)}h"
        else:
            return f"{int(hours / 24)}d"
    age_display.short_description = 'Age'
    age_display.admin_order_field = 'created_at'
    
    def recipient_profile_link(self, obj):
        if hasattr(obj.recipient, 'customer_profile'):
            url = reverse('admin:customers_customerprofile_change', args=[obj.recipient.customer_profile.id])
            return format_html('<a href=\"{}\" target=\"_blank\">View Profile</a>', url)
        return 'No profile'
    recipient_profile_link.short_description = 'Profile'
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href=\"{}\" target=\"_blank\">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Order'
    
    def shop_link(self, obj):
        if obj.shop:
            url = reverse('admin:shops_shop_change', args=[obj.shop.id])
            return format_html('<a href=\"{}\" target=\"_blank\">{}</a>', url, obj.shop.name)
        return '-'
    shop_link.short_description = 'Shop'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user_name', 'order_notifications', 'loyalty_notifications',
        'promotion_notifications', 'immediate_notifications', 'daily_digest'
    )
    list_filter = (
        'order_notifications', 'loyalty_notifications', 'promotion_notifications',
        'reminder_notifications', 'system_notifications', 'daily_digest',
        'immediate_notifications', 'created_at'
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'user_profile_link')
    ordering = ['user__username']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_profile_link')
        }),
        ('Notification Types', {
            'fields': (
                'order_notifications', 'loyalty_notifications', 
                'promotion_notifications', 'reminder_notifications', 
                'system_notifications'
            )
        }),
        ('Frequency Settings', {
            'fields': ('immediate_notifications', 'daily_digest')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        profile = getattr(obj.user, 'customer_profile', None)
        if profile and profile.preferred_name:
            return f"{profile.preferred_name} ({obj.user.username})"
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__username'
    
    def user_profile_link(self, obj):
        if hasattr(obj.user, 'customer_profile'):
            url = reverse('admin:customers_customerprofile_change', args=[obj.user.customer_profile.id])
            return format_html('<a href=\"{}\" target=\"_blank\">View Profile</a>', url)
        return 'No profile'
    user_profile_link.short_description = 'Profile'


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = (
        'title_truncated', 'template_name', 'target_count', 
        'sent_status', 'success_rate', 'created_by_name', 'created_at'
    )
    list_filter = ('is_sent', 'template__type', 'created_at', 'sent_at')
    search_fields = ('title', 'message', 'created_by__username', 'template__name')
    readonly_fields = (
        'is_sent', 'sent_count', 'failed_count', 'created_at', 
        'sent_at', 'target_count', 'success_rate', 'template_link'
    )
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    filter_horizontal = ('target_users',)
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('template', 'template_link', 'title', 'message')
        }),
        ('Targeting', {
            'fields': ('target_shop', 'target_users', 'target_count')
        }),
        ('Status & Results', {
            'fields': (
                'is_sent', 'sent_count', 'failed_count', 
                'success_rate', 'sent_at'
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'template', 'created_by', 'target_shop'
        ).prefetch_related('target_users')
    
    def title_truncated(self, obj):
        return obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
    title_truncated.short_description = 'Title'
    title_truncated.admin_order_field = 'title'
    
    def template_name(self, obj):
        return obj.template.name
    template_name.short_description = 'Template'
    template_name.admin_order_field = 'template__name'
    
    def target_count(self, obj):
        return obj.target_users.count()
    target_count.short_description = 'Target Users'
    
    def sent_status(self, obj):
        if obj.is_sent:
            color = 'green' if obj.failed_count == 0 else 'orange'
            return format_html(
                '<span style="color: {}; font-weight: bold;">SENT</span>',
                color
            )
        return format_html('<span style="color: red; font-weight: bold;">PENDING</span>')
    sent_status.short_description = 'Status'
    sent_status.admin_order_field = 'is_sent'
    
    def success_rate(self, obj):
        if obj.sent_count == 0:
            return '0%'
        rate = (obj.sent_count / (obj.sent_count + obj.failed_count)) * 100
        color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    success_rate.short_description = 'Success Rate'
    
    def created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    created_by_name.short_description = 'Created By'
    created_by_name.admin_order_field = 'created_by__username'
    
    def template_link(self, obj):
        url = reverse('admin:notifications_notificationtemplate_change', args=[obj.template.id])
        return format_html('<a href=\"{}\" target=\"_blank\">{}</a>', url, obj.template.name)
    template_link.short_description = 'Template'
