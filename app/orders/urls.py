from django.urls import path
from .views import (
    OrderListCreateView, OrderDetailView, OrderStatusUpdateView,
    shop_orders_by_status, add_order_item, remove_order_item,
    customer_order_history
)

urlpatterns = [
    # Main order endpoints
    path('', OrderListCreateView.as_view(), name='orders'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    
    # Shop owner specific endpoints
    path('status/<str:status_filter>/', shop_orders_by_status, name='orders-by-status'),
    
    # Order items management
    path('<int:order_id>/items/', add_order_item, name='add-order-item'),
    path('<int:order_id>/items/<int:item_id>/', remove_order_item, name='remove-order-item'),
    
    # Customer specific endpoints
    path('history/', customer_order_history, name='customer-order-history'),
]