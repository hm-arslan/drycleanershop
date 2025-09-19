from django.urls import path
from .views import (
    NotificationListView, NotificationUpdateView,
    NotificationPreferenceView, NotificationTemplateListView,
    NotificationTemplateDetailView, CreateBatchNotificationView,
    NotificationBatchListView, mark_all_notifications_read,
    notification_stats, notification_system_health
)

urlpatterns = [
    # User notification endpoints
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/update/', NotificationUpdateView.as_view(), name='notification-update'),
    path('mark-all-read/', mark_all_notifications_read, name='mark-all-notifications-read'),
    path('stats/', notification_stats, name='notification-stats'),
    
    # User preferences
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    
    # Admin/Shop owner endpoints
    path('templates/', NotificationTemplateListView.as_view(), name='notification-templates'),
    path('templates/<int:pk>/', NotificationTemplateDetailView.as_view(), name='notification-template-detail'),
    path('batch/create/', CreateBatchNotificationView.as_view(), name='create-batch-notification'),
    path('batch/', NotificationBatchListView.as_view(), name='notification-batches'),
    
    # System health
    path('health/', notification_system_health, name='notification-system-health'),
]