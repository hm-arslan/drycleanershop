from typing import Dict, List, Optional, Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template import Template, Context
from django.db import transaction
from django.utils.html import strip_tags
import logging

from .models import Notification, NotificationTemplate, NotificationPreference, NotificationBatch
from orders.models import Order
from shops.models import Shop

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing in-app notifications"""
    
    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        priority: str = 'normal',
        order: Optional[Order] = None,
        shop: Optional[Shop] = None,
        template: Optional[NotificationTemplate] = None,
        data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[timezone.datetime] = None
    ) -> Notification:
        """Create a single notification"""
        try:
            # Check user preferences
            prefs = NotificationService.get_user_preferences(recipient)
            
            # Skip if user has disabled this type of notification
            if template and not NotificationService._should_send_notification(prefs, template.type):
                logger.info(f"Skipping notification for user {recipient.id} - type {template.type} disabled")
                return None
            
            notification = Notification.objects.create(
                recipient=recipient,
                title=strip_tags(title)[:200],  # Sanitize and truncate
                message=strip_tags(message),
                priority=priority,
                order=order,
                shop=shop,
                template=template,
                data=data or {},
                expires_at=expires_at
            )
            
            logger.info(f"Created notification {notification.id} for user {recipient.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return None
    
    @staticmethod
    def create_from_template(
        template_name: str,
        recipient: User,
        context_data: Dict[str, Any],
        order: Optional[Order] = None,
        shop: Optional[Shop] = None,
        expires_at: Optional[timezone.datetime] = None
    ) -> Optional[Notification]:
        """Create notification from template with context data"""
        try:
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template {template_name} not found or inactive")
            return None
        
        # Render templates with context data
        title_template = Template(template.title_template)
        message_template = Template(template.message_template)
        context = Context(context_data)
        
        rendered_title = title_template.render(context)
        rendered_message = message_template.render(context)
        
        return NotificationService.create_notification(
            recipient=recipient,
            title=rendered_title,
            message=rendered_message,
            priority=template.priority,
            order=order,
            shop=shop,
            template=template,
            data=context_data,
            expires_at=expires_at
        )
    
    @staticmethod
    def create_batch_notifications(
        template_name: str,
        recipients: List[User],
        context_data: Dict[str, Any],
        created_by: User,
        shop: Optional[Shop] = None
    ) -> NotificationBatch:
        """Create batch notifications"""
        try:
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template {template_name} not found or inactive")
            return None
        
        # Render templates
        title_template = Template(template.title_template)
        message_template = Template(template.message_template)
        context = Context(context_data)
        
        rendered_title = title_template.render(context)
        rendered_message = message_template.render(context)
        
        # Create batch record
        batch = NotificationBatch.objects.create(
            template=template,
            title=rendered_title,
            message=rendered_message,
            target_shop=shop,
            created_by=created_by
        )
        batch.target_users.set(recipients)
        
        # Send notifications
        sent_count = 0
        failed_count = 0
        
        with transaction.atomic():
            for recipient in recipients:
                notification = NotificationService.create_notification(
                    recipient=recipient,
                    title=rendered_title,
                    message=rendered_message,
                    priority=template.priority,
                    shop=shop,
                    template=template,
                    data=context_data
                )
                
                if notification:
                    sent_count += 1
                else:
                    failed_count += 1
            
            # Update batch status
            batch.is_sent = True
            batch.sent_count = sent_count
            batch.failed_count = failed_count
            batch.sent_at = timezone.now()
            batch.save()
        
        logger.info(f"Batch {batch.id} sent: {sent_count} successful, {failed_count} failed")
        return batch
    
    @staticmethod
    def get_user_notifications(
        user: User,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Notification]:
        """Get user notifications with filters"""
        queryset = user.notifications.select_related('template', 'order', 'shop')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Exclude expired notifications
        from django.db import models
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | 
            models.Q(expires_at__gt=timezone.now())
        )
        
        return list(queryset[:limit])
    
    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get count of unread notifications"""
        from django.db import models
        return user.notifications.filter(
            status='unread'
        ).filter(
            models.Q(expires_at__isnull=True) | 
            models.Q(expires_at__gt=timezone.now())
        ).count()
    
    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all user notifications as read"""
        count = user.notifications.filter(status='unread').update(
            status='read',
            read_at=timezone.now()
        )
        return count
    
    @staticmethod
    def cleanup_expired_notifications(days_old: int = 30) -> int:
        """Clean up expired and old notifications"""
        from django.db import models
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        
        # Delete expired notifications or very old read/archived notifications
        expired_filter = models.Q(expires_at__lt=timezone.now())
        old_filter = models.Q(
            created_at__lt=cutoff_date,
            status__in=['read', 'archived']
        )
        
        count = Notification.objects.filter(expired_filter | old_filter).count()
        Notification.objects.filter(expired_filter | old_filter).delete()
        
        logger.info(f"Cleaned up {count} old notifications")
        return count
    
    @staticmethod
    def get_user_preferences(user: User) -> NotificationPreference:
        """Get or create user notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'order_notifications': True,
                'loyalty_notifications': True,
                'promotion_notifications': True,
                'reminder_notifications': True,
                'system_notifications': True,
                'daily_digest': False,
                'immediate_notifications': True,
            }
        )
        return prefs
    
    @staticmethod
    def _should_send_notification(prefs: NotificationPreference, notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences"""
        type_mapping = {
            'order_status': prefs.order_notifications,
            'loyalty_points': prefs.loyalty_notifications,
            'promotion': prefs.promotion_notifications,
            'reminder': prefs.reminder_notifications,
            'system': prefs.system_notifications,
            'welcome': True,  # Always send welcome notifications
        }
        
        return type_mapping.get(notification_type, True)


class OrderNotificationService:
    """Specialized service for order-related notifications"""
    
    @staticmethod
    def notify_order_status_change(order: Order, old_status: str, new_status: str):
        """Send notification when order status changes"""
        context_data = {
            'order': order,
            'order_number': order.order_number,
            'old_status': old_status,
            'new_status': new_status,
            'customer_name': order.customer.get_full_name() or order.customer.username,
            'shop_name': order.shop.name,
        }
        
        # Notify customer
        NotificationService.create_from_template(
            template_name='order_status_update',
            recipient=order.customer,
            context_data=context_data,
            order=order,
            shop=order.shop
        )
        
        # Notify shop owner if it's an important status
        if new_status in ['ready_for_pickup', 'completed']:
            NotificationService.create_from_template(
                template_name='order_status_update_shop',
                recipient=order.shop.owner,
                context_data=context_data,
                order=order,
                shop=order.shop
            )
    
    @staticmethod
    def notify_new_order(order: Order):
        """Send notification for new order"""
        context_data = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': order.customer.get_full_name() or order.customer.username,
            'shop_name': order.shop.name,
            'total_amount': order.total_amount,
        }
        
        # Notify shop owner
        NotificationService.create_from_template(
            template_name='new_order',
            recipient=order.shop.owner,
            context_data=context_data,
            order=order,
            shop=order.shop
        )
    
    @staticmethod
    def notify_order_ready(order: Order):
        """Send notification when order is ready for pickup"""
        context_data = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': order.customer.get_full_name() or order.customer.username,
            'shop_name': order.shop.name,
            'pickup_instructions': getattr(order.pickup_address, 'pickup_instructions', ''),
        }
        
        NotificationService.create_from_template(
            template_name='order_ready',
            recipient=order.customer,
            context_data=context_data,
            order=order,
            shop=order.shop
        )