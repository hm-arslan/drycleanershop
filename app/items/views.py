from rest_framework import generics, permissions
from .models import Item, ServicePrice
from .serializers import ItemSerializer, ServicePriceSerializer

class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(shop=self.request.user.shop)

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)


class ServicePriceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServicePriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServicePrice.objects.filter(shop=self.request.user.shop)

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)
