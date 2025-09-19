from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomerProfile, CustomerAddress, LoyaltyTransaction
from accounts.serializers import UserSerializer
from core.validators import validate_safe_string, validate_text_length

User = get_user_model()


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    display_name = serializers.SerializerMethodField()
    points_expiring_soon = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'user_details', 'display_name',
            'date_of_birth', 'preferred_name', 'emergency_contact_name', 'emergency_contact_phone',
            'preferred_pickup_type', 'preferred_communication', 'special_instructions',
            'loyalty_points', 'membership_tier', 'total_spent',
            'first_order_date', 'last_order_date', 'total_orders', 'average_order_value',
            'email_marketing', 'sms_marketing', 'points_expiring_soon',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'user', 'loyalty_points', 'membership_tier', 'total_spent',
            'first_order_date', 'last_order_date', 'total_orders', 'average_order_value',
            'created_at', 'updated_at'
        ]
    
    def get_display_name(self, obj):
        return obj.preferred_name or obj.user.get_full_name() or obj.user.username
    
    def get_points_expiring_soon(self, obj):
        """Get points expiring in the next 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        expiring_transactions = obj.user.loyalty_transactions.filter(
            type='earned',
            expires_at__isnull=False,
            expires_at__lte=timezone.now() + timedelta(days=30),
            expires_at__gt=timezone.now()
        )
        return sum(trans.points for trans in expiring_transactions)
    
    def validate_preferred_name(self, value):
        if value:
            validate_safe_string(value)
            validate_text_length(value, max_length=50)
        return value
    
    def validate_special_instructions(self, value):
        if value:
            validate_safe_string(value)
            validate_text_length(value, max_length=1000)
        return value


class CustomerAddressSerializer(serializers.ModelSerializer):
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerAddress
        fields = [
            'id', 'customer', 'type', 'label',
            'street_address', 'apartment_unit', 'city', 'state', 'postal_code', 'country',
            'is_default', 'pickup_instructions', 'full_address',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['customer', 'created_at', 'updated_at']
    
    def validate_label(self, value):
        validate_safe_string(value)
        validate_text_length(value, max_length=50)
        
        # Check for duplicate labels for the same customer
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            existing = CustomerAddress.objects.filter(
                customer=request.user,
                label=value
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError("You already have an address with this label.")
        
        return value
    
    def validate_street_address(self, value):
        validate_safe_string(value)
        validate_text_length(value, max_length=255)
        return value
    
    def validate_pickup_instructions(self, value):
        if value:
            validate_safe_string(value)
            validate_text_length(value, max_length=500)
        return value


class CustomerAddressCreateSerializer(CustomerAddressSerializer):
    """Serializer for creating addresses without exposing customer field"""
    
    class Meta(CustomerAddressSerializer.Meta):
        fields = [
            'id', 'type', 'label',
            'street_address', 'apartment_unit', 'city', 'state', 'postal_code', 'country',
            'is_default', 'pickup_instructions', 'full_address',
            'created_at', 'updated_at', 'is_active'
        ]


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'customer', 'customer_name', 'type', 'points', 'description',
            'order', 'order_number', 'created_at', 'expires_at',
            'processed_by', 'processed_by_name'
        ]
        read_only_fields = ['customer', 'created_at']
    
    def validate_description(self, value):
        validate_safe_string(value)
        validate_text_length(value, max_length=200)
        return value


class CustomerSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for customer lists"""
    user_details = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    default_address = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'user_details', 'display_name',
            'preferred_name', 'membership_tier', 'loyalty_points', 'total_spent',
            'total_orders', 'last_order_date', 'default_address', 'is_active'
        ]
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'phone': obj.user.phone,
        }
    
    def get_display_name(self, obj):
        return obj.preferred_name or obj.user.get_full_name() or obj.user.username
    
    def get_default_address(self, obj):
        default_addr = obj.user.addresses.filter(is_default=True, is_active=True).first()
        if default_addr:
            return {
                'id': default_addr.id,
                'label': default_addr.label,
                'full_address': default_addr.full_address
            }
        return None


class CustomerAnalyticsSerializer(serializers.Serializer):
    """Serializer for customer analytics data"""
    customer_id = serializers.IntegerField()
    display_name = serializers.CharField()
    membership_tier = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=8, decimal_places=2)
    loyalty_points = serializers.IntegerField()
    first_order_date = serializers.DateTimeField()
    last_order_date = serializers.DateTimeField()
    days_since_last_order = serializers.IntegerField()
    preferred_services = serializers.ListField(child=serializers.CharField())
    preferred_items = serializers.ListField(child=serializers.CharField())


class LoyaltyRedemptionSerializer(serializers.Serializer):
    """Serializer for loyalty point redemption"""
    points = serializers.IntegerField(min_value=1)
    description = serializers.CharField(max_length=200)
    
    def validate_points(self, value):
        # Check if customer has enough points
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            profile = getattr(request.user, 'customer_profile', None)
            if profile and profile.loyalty_points < value:
                raise serializers.ValidationError(
                    f"Insufficient points. You have {profile.loyalty_points} points available."
                )
        return value
    
    def validate_description(self, value):
        validate_safe_string(value)
        validate_text_length(value, max_length=200)
        return value