from django.urls import path
from .views import ItemListCreateView, ServicePriceListCreateView

urlpatterns = [
    path('', ItemListCreateView.as_view(), name='items'),
    path('prices/', ServicePriceListCreateView.as_view(), name='service-prices'),
]
