from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.permissions import IsShopOwner, IsAdminUser
from .models import Notification, NotificationPreference, NotificationTemplate, NotificationBatch
from .serializers import (
    NotificationSerializer, NotificationUpdateSerializer,
    NotificationPreferenceSerializer, NotificationTemplateSerializer,
    NotificationBatchSerializer, CreateBatchNotificationSerializer,
    NotificationStatsSerializer
)
from .services import NotificationService

User = get_user_model()


@method_decorator(ratelimit(key='user', rate='100/hour', method='GET'), name='get')
class NotificationListView(generics.ListAPIView):
    """List user notifications with filtering"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = self.request.user.notifications.select_related(
            'template', 'order', 'shop'
        ).filter(
            # Exclude expired notifications
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by type (via template)
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(template__type=notification_type)
        
        return queryset[:50]  # Limit to 50 most recent


@method_decorator(ratelimit(key='user', rate='200/hour', method='PATCH'), name='patch')
class NotificationUpdateView(generics.UpdateAPIView):
    """Update notification status (mark as read/archived)"""
    serializer_class = NotificationUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.notifications.all()
    
    def perform_update(self, serializer):
        notification = self.get_object()
        new_status = serializer.validated_data.get('status')
        
        if new_status == 'read':
            notification.mark_as_read()
        elif new_status == 'archived':
            notification.mark_as_archived()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='50/hour', method='POST')
def mark_all_notifications_read(request):
    """Mark all user notifications as read"""
    count = NotificationService.mark_all_as_read(request.user)
    return Response({
        'message': f'Marked {count} notifications as read',
        'count': count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='200/hour', method='GET')
def notification_stats(request):
    """Get user notification statistics"""
    user = request.user
    
    # Get counts by status
    notifications = user.notifications.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    stats = {
        'total_notifications': notifications.count(),
        'unread_count': notifications.filter(status='unread').count(),
        'read_count': notifications.filter(status='read').count(),
        'archived_count': notifications.filter(status='archived').count(),
    }
    
    # Get counts by priority
    priority_stats = notifications.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    stats['notifications_by_priority'] = {
        item['priority']: item['count'] for item in priority_stats
    }
    
    # Get counts by type
    type_stats = notifications.filter(
        template__isnull=False
    ).values('template__type').annotate(
        count=Count('id')
    ).order_by('template__type')
    stats['notifications_by_type'] = {
        item['template__type']: item['count'] for item in type_stats
    }
    
    # Get recent notifications
    recent = notifications.select_related('template', 'order', 'shop')[:10]
    stats['recent_notifications'] = NotificationSerializer(recent, many=True).data
    
    serializer = NotificationStatsSerializer(stats)
    return Response(serializer.data)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get and update user notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return NotificationService.get_user_preferences(self.request.user)


# Admin/Shop Owner views

@method_decorator(ratelimit(key='user', rate='100/hour', method='GET'), name='get')
class NotificationTemplateListView(generics.ListCreateAPIView):
    """List and create notification templates (admin only)"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    queryset = NotificationTemplate.objects.all()


@method_decorator(ratelimit(key='user', rate='50/hour', method='PATCH'), name='patch')
class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage notification templates (admin only)"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    queryset = NotificationTemplate.objects.all()


@method_decorator(ratelimit(key='user', rate='20/hour', method='POST'), name='post')
class CreateBatchNotificationView(generics.CreateAPIView):
    """Create batch notifications (shop owners and admins)"""
    serializer_class = CreateBatchNotificationSerializer
    permission_classes = [IsShopOwner]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_name = serializer.validated_data['template_name']
        context_data = serializer.validated_data.get('context_data', {})
        target_shop_id = serializer.validated_data.get('target_shop')
        target_user_ids = serializer.validated_data.get('target_users', [])
        
        # Get shop object if provided
        target_shop = None
        if target_shop_id:
            from shops.models import Shop
            try:
                target_shop = Shop.objects.get(id=target_shop_id)
                # Check permissions
                if request.user.role == 'shop_owner' and target_shop.owner != request.user:
                    return Response(
                        {'error': 'You can only send notifications for your own shop'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Shop.DoesNotExist:
                return Response(
                    {'error': 'Shop not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Determine recipients
        if target_user_ids:
            recipients = User.objects.filter(id__in=target_user_ids)
        elif target_shop:
            # Get customers who have orders at this shop
            recipients = User.objects.filter(orders__shop=target_shop).distinct()
        else:
            # Default to shop's customers if shop owner
            if request.user.role == 'shop_owner':
                user_shops = request.user.owned_shops.all()
                recipients = User.objects.filter(orders__shop__in=user_shops).distinct()
            else:
                # Admin can send to all users
                recipients = User.objects.filter(is_active=True)
        
        # Create batch
        batch = NotificationService.create_batch_notifications(
            template_name=template_name,
            recipients=list(recipients),
            context_data=context_data,
            created_by=request.user,
            shop=target_shop
        )
        
        if not batch:
            return Response(
                {'error': 'Failed to create batch notifications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = NotificationBatchSerializer(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='user', rate='100/hour', method='GET'), name='get')
class NotificationBatchListView(generics.ListAPIView):
    """List notification batches (shop owners see their own)"""
    serializer_class = NotificationBatchSerializer
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return NotificationBatch.objects.all()
        else:
            # Shop owners see their own batches
            return NotificationBatch.objects.filter(created_by=self.request.user)


# Health check endpoints

@api_view(['GET'])
@permission_classes([IsAdminUser])
def notification_system_health(request):
    """Check notification system health"""
    try:
        # Check template count
        template_count = NotificationTemplate.objects.filter(is_active=True).count()
        
        # Check recent notification activity
        recent_count = Notification.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        # Check for failed batches
        failed_batches = NotificationBatch.objects.filter(
            failed_count__gt=0,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        health_data = {
            'status': 'healthy',
            'active_templates': template_count,
            'notifications_24h': recent_count,
            'failed_batches_7d': failed_batches,
            'timestamp': timezone.now(),
        }
        
        # Mark as unhealthy if no active templates or too many failures
        if template_count == 0 or failed_batches > 10:
            health_data['status'] = 'degraded'
        
        return Response(health_data)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now(),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
