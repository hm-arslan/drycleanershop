from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from core.permissions import IsShopOwnerOrCustomer, CanTakeOrders, CanUpdateOrders, IsShopOwnerOrStaff
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderCreateSerializer, 
    OrderStatusUpdateSerializer, OrderItemSerializer
)


class OrderListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [CanTakeOrders()]
        return [IsShopOwnerOrCustomer()]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'shop_owner' and hasattr(user, 'shop'):
            # Shop owner sees all orders for their shop
            return Order.objects.filter(shop=user.shop)
        elif user.role == 'staff' and hasattr(user, 'staff_profile'):
            # Staff sees orders for their shop
            return Order.objects.filter(shop=user.staff_profile.shop)
        else:
            # Customer sees only their own orders
            return Order.objects.filter(customer=user)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsShopOwnerOrCustomer]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'shop_owner' and hasattr(user, 'shop'):
            return Order.objects.filter(shop=user.shop)
        elif user.role == 'staff' and hasattr(user, 'staff_profile'):
            return Order.objects.filter(shop=user.staff_profile.shop)
        else:
            return Order.objects.filter(customer=user)


class OrderStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [CanUpdateOrders]
    serializer_class = OrderStatusUpdateSerializer
    
    def get_queryset(self):
        # Shop owners and staff with permission can update order status
        user = self.request.user
        if user.role == 'shop_owner' and hasattr(user, 'shop'):
            return Order.objects.filter(shop=user.shop)
        elif user.role == 'staff' and hasattr(user, 'staff_profile'):
            return Order.objects.filter(shop=user.staff_profile.shop)
        return Order.objects.none()


@api_view(['GET'])
@permission_classes([IsShopOwnerOrStaff])
def shop_orders_by_status(request, status_filter):
    """Get orders filtered by status for shop owners and staff"""
    user = request.user
    
    # Get the shop based on user role
    if user.role == 'shop_owner' and hasattr(user, 'shop'):
        shop = user.shop
    elif user.role == 'staff' and hasattr(user, 'staff_profile'):
        shop = user.staff_profile.shop
    else:
        return Response(
            {"error": "Access denied"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    valid_statuses = ['received', 'in_progress', 'ready_for_pickup', 'completed', 'cancelled']
    if status_filter not in valid_statuses:
        return Response(
            {"error": f"Invalid status. Valid options: {valid_statuses}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    orders = Order.objects.filter(shop=shop, status=status_filter)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsShopOwnerOrCustomer])
def add_order_item(request, order_id):
    """Add an item to an existing order"""
    user = request.user
    
    # Get the order based on user role
    if user.role == 'shop_owner' and hasattr(user, 'shop'):
        order = get_object_or_404(Order, id=order_id, shop=user.shop)
    elif user.role == 'staff' and hasattr(user, 'staff_profile'):
        order = get_object_or_404(Order, id=order_id, shop=user.staff_profile.shop)
    else:
        order = get_object_or_404(Order, id=order_id, customer=user)
    
    # Check if order can be modified
    if order.status not in ['received']:
        return Response(
            {"error": "Cannot add items to orders that are in progress or completed"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = OrderItemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(order=order)
        order.calculate_total()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsShopOwnerOrCustomer])
def remove_order_item(request, order_id, item_id):
    """Remove an item from an order"""
    user = request.user
    
    # Get the order based on user role
    if user.role == 'shop_owner' and hasattr(user, 'shop'):
        order = get_object_or_404(Order, id=order_id, shop=user.shop)
    elif user.role == 'staff' and hasattr(user, 'staff_profile'):
        order = get_object_or_404(Order, id=order_id, shop=user.staff_profile.shop)
    else:
        order = get_object_or_404(Order, id=order_id, customer=user)
    
    # Check if order can be modified
    if order.status not in ['received']:
        return Response(
            {"error": "Cannot remove items from orders that are in progress or completed"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    item.delete()
    order.calculate_total()
    
    return Response({"message": "Item removed successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def customer_order_history(request):
    """Get order history for the authenticated customer"""
    user = request.user
    orders = Order.objects.filter(customer=user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
