from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from core.permissions import IsShopOwner
from .models import CustomerProfile, CustomerAddress, LoyaltyTransaction
from .serializers import (
    CustomerProfileSerializer, CustomerAddressSerializer, CustomerAddressCreateSerializer,
    LoyaltyTransactionSerializer, CustomerSummarySerializer, CustomerAnalyticsSerializer,
    LoyaltyRedemptionSerializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# Customer Profile Management
@method_decorator(ratelimit(key='user', rate='20/h', method=['GET', 'PUT', 'PATCH']), name='dispatch')
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        profile, created = CustomerProfile.objects.get_or_create(user=user)
        if created:
            logger.info(f'Customer profile created for user: {user.username}')
        return profile
    
    def perform_update(self, serializer):
        profile = serializer.save()
        logger.info(f'Customer profile updated for user: {self.request.user.username}')


# Customer Address Management
@method_decorator(ratelimit(key='user', rate='30/h', method=['GET', 'POST']), name='dispatch')
class CustomerAddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerAddressCreateSerializer
        return CustomerAddressSerializer
    
    def get_queryset(self):
        return CustomerAddress.objects.filter(
            customer=self.request.user,
            is_active=True
        ).order_by('-is_default', 'label')
    
    def perform_create(self, serializer):
        address = serializer.save(customer=self.request.user)
        logger.info(f'Address created: {address.label} for user {self.request.user.username}')


@method_decorator(ratelimit(key='user', rate='20/h', method=['GET', 'PUT', 'DELETE']), name='dispatch')
class CustomerAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CustomerAddress.objects.filter(
            customer=self.request.user,
            is_active=True
        )
    
    def perform_update(self, serializer):
        address = serializer.save()
        logger.info(f'Address updated: {address.label} for user {self.request.user.username}')
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()
        logger.info(f'Address deactivated: {instance.label} for user {self.request.user.username}')


# Loyalty Management
@method_decorator(ratelimit(key='user', rate='10/h', method='GET'), name='get')
class LoyaltyTransactionListView(generics.ListAPIView):
    serializer_class = LoyaltyTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LoyaltyTransaction.objects.filter(
            customer=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='5/h', method='POST')
def redeem_loyalty_points(request):
    """Redeem loyalty points"""
    serializer = LoyaltyRedemptionSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        points = serializer.validated_data['points']
        description = serializer.validated_data['description']
        
        profile = getattr(request.user, 'customer_profile', None)
        if not profile:
            return Response(
                {'error': 'Customer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if profile.redeem_loyalty_points(points, description):
            logger.info(f'Points redeemed: {points} by user {request.user.username}')
            return Response({
                'message': f'Successfully redeemed {points} points',
                'remaining_points': profile.loyalty_points
            })
        else:
            return Response(
                {'error': 'Insufficient points'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Shop Owner Views for Customer Management
@method_decorator(ratelimit(key='user', rate='50/h', method='GET'), name='get')
class ShopCustomerListView(generics.ListAPIView):
    serializer_class = CustomerSummarySerializer
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        shop = self.request.user.shop
        
        # Get customers who have placed orders at this shop
        customer_profiles = CustomerProfile.objects.filter(
            user__orders__shop=shop,
            is_active=True
        ).distinct().select_related('user').prefetch_related('user__addresses')
        
        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            customer_profiles = customer_profiles.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(preferred_name__icontains=search)
            )
        
        # Apply tier filter
        tier = self.request.query_params.get('tier')
        if tier:
            customer_profiles = customer_profiles.filter(membership_tier=tier)
        
        # Apply ordering
        ordering = self.request.query_params.get('ordering', '-last_order_date')
        if ordering:
            customer_profiles = customer_profiles.order_by(ordering)
        
        return customer_profiles


@method_decorator(ratelimit(key='user', rate='20/h', method='GET'), name='get')
class ShopCustomerDetailView(generics.RetrieveAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        shop = self.request.user.shop
        return CustomerProfile.objects.filter(
            user__orders__shop=shop,
            is_active=True
        ).distinct().select_related('user')


@api_view(['GET'])
@permission_classes([IsShopOwner])
@ratelimit(key='user', rate='10/h', method='GET')
def customer_analytics(request, customer_id):
    """Get detailed analytics for a specific customer"""
    shop = request.user.shop
    
    try:
        profile = CustomerProfile.objects.get(
            id=customer_id,
            user__orders__shop=shop,
            is_active=True
        )
    except CustomerProfile.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get customer orders for this shop
    orders = profile.user.orders.filter(shop=shop, status='completed')
    
    # Calculate analytics
    analytics_data = {
        'customer_id': profile.id,
        'display_name': profile.preferred_name or profile.user.get_full_name() or profile.user.username,
        'membership_tier': profile.membership_tier,
        'total_spent': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_orders': orders.count(),
        'average_order_value': orders.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        'loyalty_points': profile.loyalty_points,
        'first_order_date': orders.order_by('created_at').first().created_at if orders.exists() else None,
        'last_order_date': orders.order_by('-created_at').first().created_at if orders.exists() else None,
        'days_since_last_order': None,
        'preferred_services': [],
        'preferred_items': []
    }
    
    # Calculate days since last order
    if analytics_data['last_order_date']:
        analytics_data['days_since_last_order'] = (
            timezone.now() - analytics_data['last_order_date']
        ).days
    
    # Get preferred services and items
    if orders.exists():
        service_counts = {}
        item_counts = {}
        
        for order in orders.prefetch_related('items__service_price__service', 'items__service_price__item'):
            for item in order.items.all():
                service_name = item.service_price.service.name
                item_name = item.service_price.item.name
                
                service_counts[service_name] = service_counts.get(service_name, 0) + item.quantity
                item_counts[item_name] = item_counts.get(item_name, 0) + item.quantity
        
        # Get top 5 preferred services and items
        analytics_data['preferred_services'] = [
            name for name, _ in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        analytics_data['preferred_items'] = [
            name for name, _ in sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    serializer = CustomerAnalyticsSerializer(analytics_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsShopOwner])
@ratelimit(key='user', rate='5/h', method='GET')
def shop_customer_stats(request):
    """Get overall customer statistics for the shop"""
    shop = request.user.shop
    
    # Get customer profiles for this shop
    profiles = CustomerProfile.objects.filter(
        user__orders__shop=shop,
        is_active=True
    ).distinct()
    
    # Calculate stats
    stats = {
        'total_customers': profiles.count(),
        'tier_distribution': profiles.values('membership_tier').annotate(
            count=Count('id')
        ).order_by('membership_tier'),
        'new_customers_this_month': profiles.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'active_customers': profiles.filter(
            last_order_date__gte=timezone.now() - timedelta(days=90)
        ).count(),
        'total_loyalty_points_outstanding': profiles.aggregate(
            total=Sum('loyalty_points')
        )['total'] or 0,
        'average_customer_value': profiles.aggregate(
            avg=Avg('total_spent')
        )['avg'] or 0,
        'top_spenders': CustomerSummarySerializer(
            profiles.order_by('-total_spent')[:10], 
            many=True
        ).data,
        'most_loyal': CustomerSummarySerializer(
            profiles.order_by('-loyalty_points')[:10], 
            many=True
        ).data
    }
    
    return Response(stats)
