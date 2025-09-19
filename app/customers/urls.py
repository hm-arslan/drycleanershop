from django.urls import path
from .views import (
    CustomerProfileView, 
    CustomerAddressListCreateView, CustomerAddressDetailView,
    LoyaltyTransactionListView, redeem_loyalty_points,
    ShopCustomerListView, ShopCustomerDetailView,
    customer_analytics, shop_customer_stats
)

urlpatterns = [
    # Customer Profile Management
    path('profile/', CustomerProfileView.as_view(), name='customer-profile'),
    
    # Address Management
    path('addresses/', CustomerAddressListCreateView.as_view(), name='customer-addresses'),
    path('addresses/<int:pk>/', CustomerAddressDetailView.as_view(), name='customer-address-detail'),
    
    # Loyalty System
    path('loyalty/transactions/', LoyaltyTransactionListView.as_view(), name='loyalty-transactions'),
    path('loyalty/redeem/', redeem_loyalty_points, name='redeem-loyalty-points'),
    
    # Shop Owner Customer Management
    path('shop/customers/', ShopCustomerListView.as_view(), name='shop-customers'),
    path('shop/customers/<int:pk>/', ShopCustomerDetailView.as_view(), name='shop-customer-detail'),
    path('shop/customers/<int:customer_id>/analytics/', customer_analytics, name='customer-analytics'),
    path('shop/stats/', shop_customer_stats, name='shop-customer-stats'),
]