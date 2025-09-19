# Dry Cleaner Shop API Documentation

## Base URL
```
http://localhost:8000/api/
```

## API Version
Current API Version: v1 (no versioning prefix used in URLs)

## Authentication
All authenticated endpoints require a JWT Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Content Type
All POST/PUT requests should use:
```
Content-Type: application/json
```

---

## Authentication Endpoints (`/api/auth/`)

### 1. Register User
- **URL**: `POST /api/auth/register/`
- **Description**: Create a new user account
- **Authentication**: None required
- **Rate Limit**: 3/min per IP

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "role": "customer|shop_owner"
}
```

**Response (201):**
```json
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "phone": "string",
    "role": "customer",
    "is_active": true,
    "date_joined": "2025-01-01T12:00:00Z"
  },
  "message": "User created successfully"
}
```

### 2. Login
- **URL**: `POST /api/auth/login/`
- **Description**: Authenticate user and get JWT tokens
- **Authentication**: None required
- **Rate Limit**: 5/min per IP

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "customer"
  }
}
```

### 2a. Token Refresh (To Be Implemented)
- **URL**: `POST /api/auth/token/refresh/`
- **Description**: Refresh JWT access token using refresh token
- **Authentication**: None required (but requires valid refresh token)
- **Rate Limit**: 10/min per IP
- **Status**: ⚠️ **Not yet implemented** - needs to be added to URLs

**Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response (200):**
```json
{
  "access": "new_jwt_access_token",
  "refresh": "new_jwt_refresh_token"
}
```

### 2b. Logout/Token Blacklist (To Be Implemented)
- **URL**: `POST /api/auth/logout/`
- **Description**: Blacklist refresh token (logout)
- **Authentication**: Required
- **Rate Limit**: 10/min per user
- **Status**: ⚠️ **Not yet implemented** - needs to be added to URLs

**Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

### 3. User Profile
- **URL**: `GET /api/auth/profile/` - Get profile
- **URL**: `PUT /api/auth/profile/` - Update profile  
- **Description**: Get or update current user profile
- **Authentication**: Required
- **Rate Limit**: 100/hour per user

**GET Response (200):**
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "role": "customer",
  "is_active": true,
  "date_joined": "2025-01-01T12:00:00Z"
}
```

**PUT Request Body:**
```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone": "string"
}
```

---

## Shop Management Endpoints (`/api/shop/`)

### 1. Create Shop
- **URL**: `POST /api/shop/create/`
- **Description**: Create a new shop (shop owners only)
- **Authentication**: Required (shop_owner role)
- **Rate Limit**: 5/hour per user

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "phone": "string",
  "email": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "postal_code": "string",
  "country": "string",
  "operating_hours": "string",
  "services_offered": "string"
}
```

### 2. Get My Shop
- **URL**: `GET /api/shop/me/`
- **Description**: Get current user's shop details
- **Authentication**: Required (shop_owner role)

**Response (200):**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "owner": 1,
  "phone": "string",
  "email": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "postal_code": "string",
  "country": "string",
  "operating_hours": "string",
  "services_offered": "string",
  "is_active": true,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

### 3. Update Shop
- **URL**: `PUT /api/shop/me/` - Update shop details
- **Authentication**: Required (shop_owner role)
- **Rate Limit**: 10/min per user

**Request Body:**
```json
{
  "name": "string",
  "description": "string", 
  "phone": "string",
  "email": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "postal_code": "string",
  "country": "string",
  "operating_hours": "string",
  "services_offered": "string"
}
```

### 4. Delete Shop
- **URL**: `DELETE /api/shop/delete/`
- **Description**: Delete current user's shop
- **Authentication**: Required (shop_owner role)
- **Rate Limit**: 1/day per user

### 5. Staff Management

#### List/Create Staff
- **URL**: `GET /api/shop/staff/` - List shop staff
- **URL**: `POST /api/shop/staff/` - Create new staff member
- **Authentication**: Required (shop_owner role)

**GET Response (200):**
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "staff_member",
      "email": "staff@example.com",
      "first_name": "John",
      "last_name": "Staff"
    },
    "position": "clerk",
    "hire_date": "2025-01-01",
    "salary": "30000.00",
    "is_active": true,
    "permissions": ["can_register_customers"],
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

**POST Request Body:**
```json
{
  "user": 2,
  "position": "clerk|manager|assistant",
  "hire_date": "2025-01-01",
  "salary": "30000.00",
  "permissions": ["can_register_customers"]
}
```

#### Staff Detail
- **URL**: `GET /api/shop/staff/{id}/` - Get staff details
- **URL**: `PUT /api/shop/staff/{id}/` - Update staff member
- **URL**: `DELETE /api/shop/staff/{id}/` - Remove staff member
- **Authentication**: Required (shop_owner role)

### 6. Staff Customer Registration
- **URL**: `POST /api/shop/staff/register-customer/`
- **Description**: Allow staff to register customers (staff members only)
- **Authentication**: Required (staff with can_register_customers permission)

**Request Body:**
```json
{
  "username": "string",
  "email": "string", 
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string"
}
```

### 7. Staff Dashboard
- **URL**: `GET /api/shop/dashboard/`
- **Description**: Get dashboard data for staff/shop owners
- **Authentication**: Required (shop_owner or staff role)

---

## Services Management Endpoints (`/api/services/`)

### 1. List/Create Services
- **URL**: `GET /api/services/` - List services
- **URL**: `POST /api/services/` - Create service (shop owners only)
- **Authentication**: Required
- **Rate Limit**: 100/hour GET, 20/hour POST

**GET Response (200):**
```json
[
  {
    "id": 1,
    "shop": 1,
    "name": "Dry Cleaning",
    "description": "Professional dry cleaning service",
    "base_price": "15.00",
    "estimated_time": "24:00:00",
    "is_available": true,
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

**POST Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "base_price": "decimal",
  "estimated_time": "HH:MM:SS",
  "is_available": true
}
```

### 2. Service Detail
- **URL**: `GET /api/services/{id}/` - Get service
- **URL**: `PUT /api/services/{id}/` - Update service (shop owners only)
- **URL**: `DELETE /api/services/{id}/` - Delete service (shop owners only)
- **Authentication**: Required

---

## Items Management Endpoints (`/api/items/`)

### 1. List/Create Items
- **URL**: `GET /api/items/` - List items
- **URL**: `POST /api/items/` - Create item (shop owners only)
- **Authentication**: Required

**GET Response (200):**
```json
[
  {
    "id": 1,
    "shop": 1,
    "name": "Shirt",
    "description": "Cotton dress shirt",
    "category": "shirts",
    "material": "cotton",
    "care_instructions": "Dry clean only",
    "is_active": true,
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

**POST Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "category": "string",
  "material": "string",
  "care_instructions": "string",
  "is_active": true
}
```

### 2. Service Prices
- **URL**: `GET /api/items/prices/` - List service prices
- **URL**: `POST /api/items/prices/` - Create service price (shop owners only)
- **Authentication**: Required

**GET Response (200):**
```json
[
  {
    "id": 1,
    "shop": 1,
    "item": 1,
    "service": 1,
    "price": "12.50",
    "is_active": true,
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

**POST Request Body:**
```json
{
  "item": 1,
  "service": 1,
  "price": "12.50",
  "is_active": true
}
```

---

## Order Management Endpoints (`/api/orders/`)

### 1. List/Create Orders
- **URL**: `GET /api/orders/` - List orders
- **URL**: `POST /api/orders/` - Create order
- **Authentication**: Required
- **Rate Limit**: 100/hour GET, 50/hour POST

**GET Response (200):**
```json
[
  {
    "id": 1,
    "order_number": "ORD-2025-0001",
    "customer": 1,
    "customer_name": "John Doe",
    "shop": 1,
    "shop_name": "Clean Express",
    "status": "received",
    "priority": "normal",
    "pickup_date": "2025-01-02T10:00:00Z",
    "delivery_date": "2025-01-03T16:00:00Z",
    "total_amount": "45.00",
    "special_instructions": "",
    "items": [
      {
        "id": 1,
        "item_name": "Shirt",
        "service_name": "Dry Cleaning",
        "quantity": 2,
        "unit_price": "12.50",
        "total_price": "25.00"
      }
    ],
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

**POST Request Body:**
```json
{
  "shop": 1,
  "pickup_date": "2025-01-02T10:00:00Z",
  "delivery_date": "2025-01-03T16:00:00Z",
  "priority": "normal|high|urgent",
  "special_instructions": "string",
  "pickup_address": 1,
  "delivery_address": 1,
  "items": [
    {
      "item": 1,
      "service": 1,
      "quantity": 2,
      "notes": "Handle with care"
    }
  ]
}
```

### 2. Order Detail
- **URL**: `GET /api/orders/{id}/` - Get order
- **URL**: `PUT /api/orders/{id}/` - Update order
- **URL**: `DELETE /api/orders/{id}/` - Delete order
- **Authentication**: Required

### 3. Update Order Status
- **URL**: `PATCH /api/orders/{id}/status/`
- **Description**: Update order status (shop owners only)
- **Authentication**: Required (shop_owner role)

**Request Body:**
```json
{
  "status": "received|in_progress|ready_for_pickup|completed|cancelled",
  "notes": "string"
}
```

### 4. Orders by Status (Shop Owners)
- **URL**: `GET /api/orders/status/{status}/`
- **Description**: Get orders filtered by status
- **Authentication**: Required (shop_owner role)
- **Parameters**: `status` - received, in_progress, ready_for_pickup, completed, cancelled

### 5. Add Order Item
- **URL**: `POST /api/orders/{order_id}/items/`
- **Description**: Add item to existing order
- **Authentication**: Required

**Request Body:**
```json
{
  "item": 1,
  "service": 1,
  "quantity": 1,
  "notes": "string"
}
```

### 6. Remove Order Item
- **URL**: `DELETE /api/orders/{order_id}/items/{item_id}/`
- **Description**: Remove item from order
- **Authentication**: Required

### 7. Customer Order History
- **URL**: `GET /api/orders/history/`
- **Description**: Get customer's order history
- **Authentication**: Required (customer role)

---

## Customer Management Endpoints (`/api/customers/`)

### 1. Customer Profile
- **URL**: `GET /api/customers/profile/` - Get profile
- **URL**: `PUT /api/customers/profile/` - Update profile
- **Description**: Manage customer profile and preferences
- **Authentication**: Required

**GET Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "preferred_name": "John",
  "date_of_birth": "1990-01-01",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+1234567890",
  "preferred_pickup_type": "drop_off",
  "preferred_communication": "email",
  "special_instructions": "",
  "loyalty_points": 150,
  "membership_tier": "silver",
  "total_spent": "500.00",
  "total_orders": 10,
  "email_marketing": true,
  "sms_marketing": false,
  "created_at": "2025-01-01T12:00:00Z"
}
```

### 2. Customer Addresses
- **URL**: `GET /api/customers/addresses/` - List addresses
- **URL**: `POST /api/customers/addresses/` - Create address
- **Authentication**: Required

**GET Response (200):**
```json
[
  {
    "id": 1,
    "type": "home",
    "label": "Home",
    "street_address": "123 Main St",
    "apartment_unit": "Apt 2B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "is_default": true,
    "pickup_instructions": "",
    "full_address": "123 Main St, Apt 2B, New York, NY 10001, USA",
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

### 3. Address Detail
- **URL**: `GET /api/customers/addresses/{id}/` - Get address
- **URL**: `PUT /api/customers/addresses/{id}/` - Update address
- **URL**: `DELETE /api/customers/addresses/{id}/` - Delete address
- **Authentication**: Required

### 4. Loyalty Transactions
- **URL**: `GET /api/customers/loyalty/transactions/`
- **Description**: Get customer's loyalty transaction history
- **Authentication**: Required

**Response (200):**
```json
[
  {
    "id": 1,
    "type": "earned",
    "points": 50,
    "description": "Points earned for order ORD-2025-0001",
    "order": 1,
    "created_at": "2025-01-01T12:00:00Z",
    "expires_at": "2026-01-01T12:00:00Z"
  }
]
```

### 5. Redeem Loyalty Points
- **URL**: `POST /api/customers/loyalty/redeem/`
- **Description**: Redeem loyalty points
- **Authentication**: Required
- **Rate Limit**: 10/hour per user

**Request Body:**
```json
{
  "points": 100,
  "description": "Discount for order ORD-2025-0002",
  "order": 2
}
```

### 6. Shop Customer Management (Shop Owners)
- **URL**: `GET /api/customers/shop/customers/` - List shop customers
- **URL**: `GET /api/customers/shop/customers/{id}/` - Get customer detail
- **Authentication**: Required (shop_owner role)

### 7. Customer Analytics (Shop Owners)
- **URL**: `GET /api/customers/shop/customers/{customer_id}/analytics/`
- **Description**: Get customer analytics and insights
- **Authentication**: Required (shop_owner role)

### 8. Shop Customer Stats (Shop Owners)
- **URL**: `GET /api/customers/shop/stats/`
- **Description**: Get aggregated customer statistics
- **Authentication**: Required (shop_owner role)

---

## Notification Endpoints (`/api/notifications/`)

### 1. List Notifications
- **URL**: `GET /api/notifications/`
- **Description**: Get user notifications with filtering
- **Authentication**: Required
- **Query Parameters**:
  - `status` - unread, read, archived
  - `priority` - low, normal, high, urgent
  - `type` - order_status, loyalty_points, promotion, reminder, system, welcome

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Order Ready for Pickup",
    "message": "Your order ORD-2025-0001 is ready for pickup",
    "priority": "normal",
    "status": "unread",
    "order": 1,
    "order_number": "ORD-2025-0001",
    "shop": 1,
    "shop_name": "Clean Express",
    "template_name": "order_ready",
    "template_type": "order_status",
    "data": {},
    "created_at": "2025-01-01T12:00:00Z",
    "expires_at": null,
    "age_in_hours": 2.5,
    "is_expired": false
  }
]
```

### 2. Update Notification Status
- **URL**: `PATCH /api/notifications/{id}/update/`
- **Description**: Mark notification as read or archived
- **Authentication**: Required

**Request Body:**
```json
{
  "status": "read|archived"
}
```

### 3. Mark All Notifications as Read
- **URL**: `POST /api/notifications/mark-all-read/`
- **Description**: Mark all user notifications as read
- **Authentication**: Required

**Response (200):**
```json
{
  "message": "Marked 5 notifications as read",
  "count": 5
}
```

### 4. Notification Statistics
- **URL**: `GET /api/notifications/stats/`
- **Description**: Get user notification statistics
- **Authentication**: Required

**Response (200):**
```json
{
  "total_notifications": 15,
  "unread_count": 3,
  "read_count": 10,
  "archived_count": 2,
  "notifications_by_priority": {
    "normal": 10,
    "high": 4,
    "urgent": 1
  },
  "notifications_by_type": {
    "order_status": 8,
    "loyalty_points": 3,
    "promotion": 2,
    "system": 2
  },
  "recent_notifications": []
}
```

### 5. Notification Preferences
- **URL**: `GET /api/notifications/preferences/` - Get preferences
- **URL**: `PUT /api/notifications/preferences/` - Update preferences
- **Description**: Manage notification preferences
- **Authentication**: Required

**GET Response (200):**
```json
{
  "order_notifications": true,
  "loyalty_notifications": true,
  "promotion_notifications": true,
  "reminder_notifications": true,
  "system_notifications": true,
  "daily_digest": false,
  "immediate_notifications": true,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

### 6. Notification Templates (Admin Only)
- **URL**: `GET /api/notifications/templates/` - List templates
- **URL**: `POST /api/notifications/templates/` - Create template
- **Authentication**: Required (admin role)

### 7. Template Detail (Admin Only)
- **URL**: `GET /api/notifications/templates/{id}/` - Get template
- **URL**: `PUT /api/notifications/templates/{id}/` - Update template
- **URL**: `DELETE /api/notifications/templates/{id}/` - Delete template
- **Authentication**: Required (admin role)

### 8. Create Batch Notifications (Shop Owners/Admin)
- **URL**: `POST /api/notifications/batch/create/`
- **Description**: Send notifications to multiple users
- **Authentication**: Required (shop_owner or admin role)
- **Rate Limit**: 20/hour per user

**Request Body:**
```json
{
  "template_name": "promotion_announcement",
  "context_data": {
    "discount_percentage": 20,
    "valid_until": "2025-01-31"
  },
  "target_shop": 1,
  "target_users": [1, 2, 3]
}
```

### 9. List Notification Batches (Shop Owners/Admin)
- **URL**: `GET /api/notifications/batch/`
- **Description**: List notification batches
- **Authentication**: Required (shop_owner or admin role)

### 10. System Health (Admin Only)
- **URL**: `GET /api/notifications/health/`
- **Description**: Check notification system health
- **Authentication**: Required (admin role)

---

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "details": "Additional error details",
  "field_errors": {
    "field_name": ["Field-specific error message"]
  }
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created successfully  
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Rate limits are applied per user or per IP address:
- Registration: 3 requests/minute per IP
- Login: 5 requests/minute per IP  
- General API: 1000 requests/hour per user
- Creating orders: 50 requests/hour per user
- Batch notifications: 20 requests/hour per user

When rate limit is exceeded:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Pagination

List endpoints support pagination with query parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Paginated Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/orders/?page=3",
  "previous": "http://localhost:8000/api/orders/?page=1", 
  "results": []
}
```

---

## Security Features

- JWT authentication with access/refresh tokens
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS protection
- SQL injection protection
- XSS prevention
- CSRF protection
- Security headers middleware
- Account lockout protection
- Request logging and monitoring