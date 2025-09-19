from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_active', 'date_joined', 'last_login_info')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'last_login_ip', 'failed_login_attempts')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'role', 'failed_login_attempts', 'account_locked_until', 'last_login_ip')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'role')
        }),
    )
    
    def last_login_info(self, obj):
        if obj.last_login and obj.last_login_ip:
            return format_html(
                '<strong>{}</strong><br/>IP: {}', 
                obj.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                obj.last_login_ip
            )
        return 'Never'
    last_login_info.short_description = 'Last Login Info'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(role='customer')  # Non-superusers can only see customers
