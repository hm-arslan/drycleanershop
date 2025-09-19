from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from core.permissions import IsShopOwner
from .models import Service
from .serializers import ServiceSerializer
import logging

logger = logging.getLogger(__name__)

@method_decorator(ratelimit(key='user', rate='20/h', method=['GET', 'POST']), name='dispatch')
class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsShopOwner]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'shop'):
            logger.warning(f'User {user.username} tried to access services without owning a shop')
            return Service.objects.none()
        return Service.objects.filter(shop=user.shop)

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'shop'):
            raise ValidationError({"error": "You need to create a shop first before adding services."})
        
        service = serializer.save(shop=user.shop)
        logger.info(f'New service created: {service.name} for shop {user.shop.name}')


@method_decorator(ratelimit(key='user', rate='10/h', method=['GET', 'PUT', 'DELETE']), name='dispatch')
class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'shop'):
            return Service.objects.none()
        return Service.objects.filter(shop=user.shop)
    
    def perform_update(self, serializer):
        service = serializer.save()
        logger.info(f'Service updated: {service.name} for shop {self.request.user.shop.name}')
    
    def perform_destroy(self, instance):
        service_name = instance.name
        shop_name = instance.shop.name
        instance.delete()
        logger.info(f'Service deleted: {service_name} from shop {shop_name}')
