from django.urls import path
from .views import (
    ShopCreateView, ShopDetailView, ShopDeleteView,
    StaffListCreateView, StaffDetailView, staff_register_customer,
    staff_dashboard
)

urlpatterns = [
    # Shop management
    path('create/', ShopCreateView.as_view(), name='create-shop'),
    path('me/', ShopDetailView.as_view(), name='my-shop'),
    path('delete/', ShopDeleteView.as_view(), name='delete-shop'),
    
    # Staff management (shop owners only)
    path('staff/', StaffListCreateView.as_view(), name='shop-staff'),
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='shop-staff-detail'),
    
    # Staff functionality
    path('staff/register-customer/', staff_register_customer, name='staff-register-customer'),
    path('dashboard/', staff_dashboard, name='staff-dashboard'),
]
