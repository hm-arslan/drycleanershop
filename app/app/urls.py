from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/shop/', include('shops.urls')),
    path('api/services/', include('services.urls')),
    path('api/items/', include('items.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/notifications/', include('notifications.urls')),
]
