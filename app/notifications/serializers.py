from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, NotificationTemplate, NotificationPreference, NotificationBatch

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    age_in_hours = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_type = serializers.CharField(source='template.type', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'priority', 'status',
            'order', 'order_number', 'shop', 'shop_name',
            'template_name', 'template_type', 'data',
            'created_at', 'read_at', 'expires_at',
            'age_in_hours', 'is_expired'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'age_in_hours', 'is_expired',
            'template_name', 'template_type', 'order_number', 'shop_name'
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification status"""
    
    class Meta:
        model = Notification
        fields = ['status']
        
    def validate_status(self, value):
        if value not in ['read', 'archived']:
            raise serializers.ValidationError("Status can only be updated to 'read' or 'archived'")
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'order_notifications', 'loyalty_notifications', 
            'promotion_notifications', 'reminder_notifications',
            'system_notifications', 'daily_digest', 'immediate_notifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates (admin only)"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'type', 'title_template', 
            'message_template', 'priority', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationBatchSerializer(serializers.ModelSerializer):
    """Serializer for notification batches"""
    target_user_count = serializers.IntegerField(source='target_users.count', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    shop_name = serializers.CharField(source='target_shop.name', read_only=True)
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'template', 'template_name', 'title', 'message',
            'target_shop', 'shop_name', 'target_user_count',
            'is_sent', 'sent_count', 'failed_count',
            'created_by', 'created_by_name', 'created_at', 'sent_at'
        ]
        read_only_fields = [
            'id', 'is_sent', 'sent_count', 'failed_count',
            'created_by', 'created_at', 'sent_at',
            'template_name', 'shop_name', 'target_user_count', 'created_by_name'
        ]


class CreateBatchNotificationSerializer(serializers.Serializer):
    """Serializer for creating batch notifications"""
    template_name = serializers.CharField(max_length=100)
    context_data = serializers.JSONField(default=dict)
    target_shop = serializers.IntegerField(required=False, allow_null=True)
    target_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    def validate_template_name(self, value):
        """Validate that template exists and is active"""
        if not NotificationTemplate.objects.filter(name=value, is_active=True).exists():
            raise serializers.ValidationError("Template not found or inactive")
        return value
    
    def validate_target_users(self, value):
        """Validate that all target users exist"""
        if value:
            existing_count = User.objects.filter(id__in=value).count()
            if existing_count != len(value):
                raise serializers.ValidationError("Some target users do not exist")
        return value


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    archived_count = serializers.IntegerField()
    notifications_by_priority = serializers.DictField()
    notifications_by_type = serializers.DictField()
    recent_notifications = NotificationSerializer(many=True)