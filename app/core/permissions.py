from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsShopOwner(permissions.BasePermission):
    """
    Custom permission to only allow shop owners to access their own shop data.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'shop_owner' and hasattr(request.user, 'shop')
        )
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        if hasattr(obj, 'shop'):
            return obj.shop == request.user.shop
        return obj == request.user.shop


class IsShopOwnerOrCustomer(permissions.BasePermission):
    """
    Permission that allows shop owners to see all their orders,
    and customers to see only their own orders.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Shop owners can access orders for their shop
        if user.role == 'shop_owner' and hasattr(user, 'shop') and hasattr(obj, 'shop'):
            return obj.shop == user.shop
            
        # Staff can access orders for their shop
        if user.role == 'staff' and hasattr(user, 'staff_profile') and hasattr(obj, 'shop'):
            return obj.shop == user.staff_profile.shop
            
        # Customers can access their own orders
        if hasattr(obj, 'customer'):
            return obj.customer == user
            
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'customer'):
            return obj.customer == request.user
        
        return False


class IsStaffOrOwner(permissions.BasePermission):
    """
    Permission that allows staff members and owners full access.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.role in ['admin', 'shop_owner'] or
            (request.user.role == 'staff' and hasattr(request.user, 'staff_profile'))
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permission that allows only admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.role == 'admin'
        )


class IsShopStaff(permissions.BasePermission):
    """
    Permission that allows shop staff members to access shop data.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'staff' and 
            hasattr(request.user, 'staff_profile') and
            request.user.staff_profile.is_active
        )
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        
        staff_profile = request.user.staff_profile
        
        # Check if object belongs to the staff member's shop
        if hasattr(obj, 'shop'):
            return obj.shop == staff_profile.shop
        elif hasattr(obj, 'customer') and hasattr(obj.customer, 'orders'):
            # For customer objects, check if customer has orders in staff's shop
            return obj.customer.orders.filter(shop=staff_profile.shop).exists()
        
        return False


class IsShopOwnerOrStaff(permissions.BasePermission):
    """
    Permission that allows shop owners and their staff to access shop data.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            # Shop owner
            (request.user.role == 'shop_owner' and hasattr(request.user, 'shop')) or
            # Shop staff
            (request.user.role == 'staff' and hasattr(request.user, 'staff_profile') and 
             request.user.staff_profile.is_active)
        )
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        
        user = request.user
        
        # Shop owner access
        if user.role == 'shop_owner' and hasattr(user, 'shop'):
            if hasattr(obj, 'shop'):
                return obj.shop == user.shop
            return obj == user.shop
        
        # Staff access
        if user.role == 'staff' and hasattr(user, 'staff_profile'):
            staff_profile = user.staff_profile
            if hasattr(obj, 'shop'):
                return obj.shop == staff_profile.shop
            elif hasattr(obj, 'customer'):
                # Allow access to customers who have orders in staff's shop
                return obj.customer.orders.filter(shop=staff_profile.shop).exists()
        
        return False


class CanTakeOrders(permissions.BasePermission):
    """
    Permission that allows taking orders (shop owners and staff with can_take_orders permission).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Shop owner can always take orders
        if request.user.role == 'shop_owner' and hasattr(request.user, 'shop'):
            return True
            
        # Staff member with can_take_orders permission
        if (request.user.role == 'staff' and 
            hasattr(request.user, 'staff_profile') and
            request.user.staff_profile.is_active and
            request.user.staff_profile.can_take_orders):
            return True
            
        return False


class CanUpdateOrders(permissions.BasePermission):
    """
    Permission that allows updating orders (shop owners and staff with can_update_orders permission).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Shop owner can always update orders
        if request.user.role == 'shop_owner' and hasattr(request.user, 'shop'):
            return True
            
        # Staff member with can_update_orders permission
        if (request.user.role == 'staff' and 
            hasattr(request.user, 'staff_profile') and
            request.user.staff_profile.is_active and
            request.user.staff_profile.can_update_orders):
            return True
            
        return False


class CanRegisterCustomers(permissions.BasePermission):
    """
    Permission that allows registering customers (shop owners and staff with can_register_customers permission).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Shop owner can always register customers
        if request.user.role == 'shop_owner' and hasattr(request.user, 'shop'):
            return True
            
        # Staff member with can_register_customers permission
        if (request.user.role == 'staff' and 
            hasattr(request.user, 'staff_profile') and
            request.user.staff_profile.is_active and
            request.user.staff_profile.can_register_customers):
            return True
            
        return False