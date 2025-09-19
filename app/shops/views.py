from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from core.permissions import IsShopOwner, CanRegisterCustomers, IsShopOwnerOrStaff
from .models import Shop, ShopStaff
from .serializers import (
    ShopSerializer, ShopStaffSerializer, CreateStaffSerializer,
    StaffCustomerRegistrationSerializer
)
import logging

User = get_user_model()

logger = logging.getLogger(__name__)

@method_decorator(ratelimit(key='user', rate='1/m', method='POST'), name='post')
class ShopCreateView(generics.CreateAPIView):
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'shop'):
            logger.warning(f'User {user.username} attempted to create multiple shops')
            raise ValidationError({"error": "You already have a shop. Each user can only own one shop."})
        
        shop = serializer.save(owner=user)
        logger.info(f'New shop created: {shop.name} by user {user.username}')
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                exc.detail if hasattr(exc, 'detail') else {'error': str(exc)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

@method_decorator(ratelimit(key='user', rate='10/m', method=['GET', 'PUT', 'PATCH']), name='dispatch')
class ShopDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ShopSerializer
    permission_classes = [IsShopOwner]

    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'shop'):
            logger.warning(f'User {user.username} tried to access shop details without owning a shop')
            raise ValidationError({"error": "You don't have a shop yet. Please create one first."})
        return user.shop
    
    def perform_update(self, serializer):
        shop = serializer.save()
        logger.info(f'Shop updated: {shop.name} by user {self.request.user.username}')


@method_decorator(ratelimit(key='user', rate='1/h', method='DELETE'), name='delete')
class ShopDeleteView(generics.DestroyAPIView):
    permission_classes = [IsShopOwner]
    
    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'shop'):
            raise ValidationError({"error": "You don't have a shop to delete."})
        return user.shop
    
    def perform_destroy(self, instance):
        shop_name = instance.name
        user = self.request.user
        instance.delete()
        logger.info(f'Shop deleted: {shop_name} by user {user.username}')


# Staff Management Views

@method_decorator(ratelimit(key='user', rate='20/hour', method='GET'), name='get')
@method_decorator(ratelimit(key='user', rate='10/hour', method='POST'), name='post')
class StaffListCreateView(generics.ListCreateAPIView):
    """List and create staff members (shop owners only)"""
    permission_classes = [IsShopOwner]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateStaffSerializer
        return ShopStaffSerializer
    
    def get_queryset(self):
        return self.request.user.shop.staff_members.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['shop'] = self.request.user.shop
        return context
    
    def perform_create(self, serializer):
        staff = serializer.save()
        logger.info(f'New staff member created: {staff.user.username} for shop {staff.shop.name}')


@method_decorator(ratelimit(key='user', rate='50/hour', method=['GET', 'PUT', 'PATCH']), name='dispatch')
@method_decorator(ratelimit(key='user', rate='5/hour', method='DELETE'), name='delete')
class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage individual staff members (shop owners only)"""
    serializer_class = ShopStaffSerializer
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        return self.request.user.shop.staff_members.all()
    
    def perform_update(self, serializer):
        staff = serializer.save()
        logger.info(f'Staff member updated: {staff.user.username} by {self.request.user.username}')
    
    def perform_destroy(self, instance):
        staff_name = instance.user.get_full_name() or instance.user.username
        user = instance.user
        shop_name = instance.shop.name
        
        # Delete the user account as well
        instance.delete()
        user.delete()
        
        logger.info(f'Staff member deleted: {staff_name} from shop {shop_name}')


@api_view(['POST'])
@permission_classes([CanRegisterCustomers])
@ratelimit(key='user', rate='20/hour', method='POST')
def staff_register_customer(request):
    """Allow staff to register new customers"""
    serializer = StaffCustomerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Log the action
        staff_name = request.user.get_full_name() or request.user.username
        logger.info(f'Customer {user.username} registered by staff {staff_name}')
        
        # Return customer data
        from accounts.serializers import UserSerializer
        user_serializer = UserSerializer(user)
        
        return Response({
            'message': 'Customer registered successfully',
            'customer': user_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsShopOwnerOrStaff])
@ratelimit(key='user', rate='100/hour', method='GET')
def staff_dashboard(request):
    """Staff dashboard with relevant information"""
    user = request.user
    
    if user.role == 'staff':
        staff_profile = user.staff_profile
        shop = staff_profile.shop
        
        # Get staff-specific stats
        from orders.models import Order
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # Orders stats for the staff member's shop
        total_orders = Order.objects.filter(shop=shop).count()
        recent_orders = Order.objects.filter(
            shop=shop, 
            created_at__date__gte=week_ago
        ).count()
        
        pending_orders = Order.objects.filter(
            shop=shop, 
            status__in=['received', 'in_progress']
        ).count()
        
        dashboard_data = {
            'user_info': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'role': user.role,
            },
            'staff_info': {
                'position': staff_profile.position,
                'hire_date': staff_profile.hire_date,
                'permissions': staff_profile.get_permissions(),
                'is_active': staff_profile.is_active,
            },
            'shop_info': {
                'id': shop.id,
                'name': shop.name,
                'address': shop.address,
            },
            'stats': {
                'total_orders': total_orders,
                'recent_orders_7d': recent_orders,
                'pending_orders': pending_orders,
            }
        }
        
        return Response(dashboard_data)
    
    elif user.role == 'shop_owner':
        shop = user.shop
        
        # Shop owner dashboard with staff info
        staff_count = shop.staff_members.filter(is_active=True).count()
        total_staff = shop.staff_members.count()
        
        dashboard_data = {
            'user_info': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'role': user.role,
            },
            'shop_info': {
                'id': shop.id,
                'name': shop.name,
                'address': shop.address,
            },
            'staff_stats': {
                'active_staff': staff_count,
                'total_staff': total_staff,
            }
        }
        
        return Response(dashboard_data)
    
    return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
