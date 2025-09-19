from rest_framework import serializers
from django.utils import timezone
from .models import Order, OrderItem, OrderStatusHistory
from items.models import ServicePrice
from items.serializers import ServicePriceSerializer
from accounts.serializers import UserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    service_price_details = ServicePriceSerializer(source='service_price', read_only=True)
    service_price_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'service_price_id', 'service_price_details', 
            'quantity', 'unit_price', 'total_price', 'notes'
        ]
        read_only_fields = ['unit_price', 'total_price']
    
    def validate_service_price_id(self, value):
        try:
            service_price = ServicePrice.objects.get(id=value)
            # Ensure the service price belongs to the same shop as the order
            if hasattr(self.context.get('request'), 'user'):
                user = self.context['request'].user
                if hasattr(user, 'shop') and service_price.shop != user.shop:
                    raise serializers.ValidationError("Service price does not belong to your shop")
            return value
        except ServicePrice.DoesNotExist:
            raise serializers.ValidationError("Service price not found")


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_details = UserSerializer(source='changed_by', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'changed_by_details', 'changed_at', 'notes']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_details = UserSerializer(source='customer', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'pickup_type',
            'customer', 'customer_details', 'shop',
            'customer_name', 'customer_phone', 'pickup_address',
            'special_instructions', 'estimated_completion',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at',
            'subtotal', 'tax_amount', 'total_amount',
            'items', 'status_history'
        ]
        read_only_fields = [
            'order_number', 'shop', 'subtotal', 'tax_amount', 'total_amount',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'pickup_type', 'customer_name', 'customer_phone', 
            'pickup_address', 'special_instructions', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Create order
        order = Order.objects.create(
            customer=user,
            shop=user.shop if hasattr(user, 'shop') else None,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            service_price_id = item_data.pop('service_price_id')
            service_price = ServicePrice.objects.get(id=service_price_id)
            OrderItem.objects.create(
                order=order,
                service_price=service_price,
                **item_data
            )
        
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = ['status', 'notes', 'estimated_completion']
    
    def update(self, instance, validated_data):
        notes = validated_data.pop('notes', '')
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Update order
        instance = super().update(instance, validated_data)
        
        # Create status history entry if status changed
        if old_status != new_status:
            OrderStatusHistory.objects.create(
                order=instance,
                status=new_status,
                changed_by=self.context['request'].user,
                notes=notes
            )
            
            # Update timestamps based on status
            if new_status == 'confirmed':
                instance.confirmed_at = timezone.now()
            elif new_status == 'completed':
                instance.completed_at = timezone.now()
            
            instance.save()
        
        return instance