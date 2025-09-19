from rest_framework import serializers
from .models import Item, ServicePrice

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'created_at']


class ServicePriceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = ServicePrice
        fields = ['id', 'service', 'service_name', 'item', 'item_name', 'price']
