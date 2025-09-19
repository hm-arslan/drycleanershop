from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Shop, ShopStaff

User = get_user_model()


class ShopSerializer(serializers.ModelSerializer):
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'address', 'phone', 'created_at', 'staff_count']
    
    def get_staff_count(self, obj):
        return obj.staff_members.filter(is_active=True).count()


class ShopStaffSerializer(serializers.ModelSerializer):
    """Serializer for viewing staff members"""
    user_info = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopStaff
        fields = [
            'id', 'user', 'user_info', 'position', 'is_active',
            'can_take_orders', 'can_update_orders', 'can_register_customers',
            'hourly_rate', 'hire_date', 'notes', 'permissions', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'hire_date', 'created_at']
    
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'phone': obj.user.phone,
            'full_name': obj.user.get_full_name() or obj.user.username
        }
    
    def get_permissions(self, obj):
        return obj.get_permissions()


class CreateStaffSerializer(serializers.Serializer):
    """Serializer for creating new staff members"""
    # User information
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Staff information
    position = serializers.CharField(max_length=100)
    can_take_orders = serializers.BooleanField(default=True)
    can_update_orders = serializers.BooleanField(default=True)
    can_register_customers = serializers.BooleanField(default=True)
    hourly_rate = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False, 
        allow_null=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'phone': validated_data['phone'],
            'password': validated_data['password'],
            'role': 'staff'
        }
        
        # Extract staff data
        staff_data = {
            'position': validated_data['position'],
            'can_take_orders': validated_data.get('can_take_orders', True),
            'can_update_orders': validated_data.get('can_update_orders', True),
            'can_register_customers': validated_data.get('can_register_customers', True),
            'hourly_rate': validated_data.get('hourly_rate'),
            'notes': validated_data.get('notes', ''),
        }
        
        # Get the shop from the request context
        shop = self.context['shop']
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(**user_data)
            
            # Create staff profile
            staff = ShopStaff.objects.create(
                shop=shop,
                user=user,
                **staff_data
            )
        
        return staff


class StaffCustomerRegistrationSerializer(serializers.Serializer):
    """Serializer for staff to register customers"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    
    # Optional customer profile fields
    preferred_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    preferred_pickup_type = serializers.ChoiceField(
        choices=[('drop_off', 'Drop Off'), ('pickup', 'Pickup Service')],
        default='drop_off'
    )
    preferred_communication = serializers.ChoiceField(
        choices=[('email', 'Email'), ('sms', 'SMS'), ('phone', 'Phone Call'), ('app', 'App Notification')],
        default='email'
    )
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value
    
    def create(self, validated_data):
        from customers.models import CustomerProfile
        
        # Extract user data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'phone': validated_data['phone'],
            'password': validated_data['password'],
            'role': 'customer'
        }
        
        # Extract profile data
        profile_data = {
            'preferred_name': validated_data.get('preferred_name', ''),
            'date_of_birth': validated_data.get('date_of_birth'),
            'preferred_pickup_type': validated_data.get('preferred_pickup_type', 'drop_off'),
            'preferred_communication': validated_data.get('preferred_communication', 'email'),
        }
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(**user_data)
            
            # Create customer profile
            profile = CustomerProfile.objects.create(
                user=user,
                **profile_data
            )
        
        return user