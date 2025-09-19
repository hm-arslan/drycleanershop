from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import patch
import random

from orders.models import Order, OrderItem, OrderStatusHistory
from shops.models import Shop
from services.models import Service
from items.models import Item, ServicePrice

User = get_user_model()


class OrderModelTest(TestCase):
    """Comprehensive unit tests for the Order model"""
    
    def setUp(self):
        """Set up test data for each test method"""
        # Create test user (customer)
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            phone='555-0100'
        )
        
        # Create test user (shop owner)
        self.shop_owner = User.objects.create_user(
            username='shopowner',
            email='owner@test.com',
            password='testpass123',
            phone='555-0101'
        )
        
        # Create test shop
        self.shop = Shop.objects.create(
            owner=self.shop_owner,
            name='Test Dry Cleaners',
            address='123 Test Street, Test City',
            phone='555-0123'
        )
        
        # Create test service
        self.service = Service.objects.create(
            shop=self.shop,
            name='Dry Clean',
            description='Professional dry cleaning service'
        )
        
        # Create test item
        self.item = Item.objects.create(
            shop=self.shop,
            name='Shirt',
            description='Dress shirt'
        )
        
        # Create test service price
        self.service_price = ServicePrice.objects.create(
            shop=self.shop,
            service=self.service,
            item=self.item,
            price=Decimal('15.99')
        )
    
    def test_order_creation_with_valid_data(self):
        """Test creating an order with valid data"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            pickup_type='drop_off',
            special_instructions='Handle with care'
        )
        
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.shop, self.shop)
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.customer_phone, '555-0456')
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.pickup_type, 'drop_off')
        self.assertEqual(order.special_instructions, 'Handle with care')
        self.assertEqual(order.subtotal, Decimal('0.00'))
        self.assertEqual(order.total_amount, Decimal('0.00'))
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)
        
    def test_order_number_generation(self):
        """Test automatic order number generation"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        # Order number should be generated automatically
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith(str(self.shop.id)))
        # New format: shop_id + 10-digit timestamp + 2-digit random suffix
        expected_length = len(str(self.shop.id)) + 10 + 2
        self.assertEqual(len(order.order_number), expected_length)
    
    def test_order_number_uniqueness(self):
        """Test that order numbers are unique"""
        # Create two orders at slightly different times
        order1 = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)
        
        order2 = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='Jane Doe',
            customer_phone='555-0789'
        )
        
        self.assertNotEqual(order1.order_number, order2.order_number)
    
    def test_order_with_custom_order_number(self):
        """Test creating order with custom order number"""
        custom_number = 'CUSTOM123'
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            order_number=custom_number
        )
        
        self.assertEqual(order.order_number, custom_number)
    
    def test_order_status_choices(self):
        """Test all valid order status choices"""
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'ready', 'completed', 'cancelled']
        
        for status in valid_statuses:
            order = Order.objects.create(
                customer=self.customer,
                shop=self.shop,
                customer_name='John Doe',
                customer_phone='555-0456',
                status=status
            )
            self.assertEqual(order.status, status)
    
    def test_pickup_type_choices(self):
        """Test all valid pickup type choices"""
        valid_pickup_types = ['drop_off', 'pickup']
        
        for pickup_type in valid_pickup_types:
            order = Order.objects.create(
                customer=self.customer,
                shop=self.shop,
                customer_name='John Doe',
                customer_phone='555-0456',
                pickup_type=pickup_type
            )
            self.assertEqual(order.pickup_type, pickup_type)
    
    def test_order_with_pickup_address(self):
        """Test order with pickup service and address"""
        pickup_address = '456 Customer Street, Customer City'
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            pickup_type='pickup',
            pickup_address=pickup_address
        )
        
        self.assertEqual(order.pickup_type, 'pickup')
        self.assertEqual(order.pickup_address, pickup_address)
    
    def test_calculate_total_method(self):
        """Test the calculate_total method"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        # Create order items
        OrderItem.objects.create(
            order=order,
            service_price=self.service_price,
            quantity=2,
            unit_price=Decimal('15.99')
        )
        
        OrderItem.objects.create(
            order=order,
            service_price=self.service_price,
            quantity=1,
            unit_price=Decimal('25.50')
        )
        
        # Manually call calculate_total (usually called by OrderItem.save())
        order.calculate_total()
        
        expected_subtotal = Decimal('57.48')  # (15.99 * 2) + 25.50
        expected_total = expected_subtotal
        
        order.refresh_from_db()
        self.assertEqual(order.subtotal, expected_subtotal)
        self.assertEqual(order.total_amount, expected_total)
    
    def test_calculate_total_with_no_items(self):
        """Test calculate_total method with no order items"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        order.calculate_total()
        
        self.assertEqual(order.subtotal, Decimal('0.00'))
        self.assertEqual(order.total_amount, Decimal('0.00'))
    
    def test_order_string_representation(self):
        """Test the __str__ method of Order model"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            order_number='TEST123'
        )
        
        expected_str = 'Order #TEST123 - John Doe'
        self.assertEqual(str(order), expected_str)
    
    def test_order_meta_ordering(self):
        """Test that orders are ordered by created_at descending"""
        # Create orders with different timestamps
        order1 = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='First Order',
            customer_phone='555-0001'
        )
        
        import time
        time.sleep(0.01)
        
        order2 = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='Second Order',
            customer_phone='555-0002'
        )
        
        orders = list(Order.objects.all())
        self.assertEqual(orders[0], order2)  # Most recent first
        self.assertEqual(orders[1], order1)
    
    def test_order_cascade_delete_with_customer(self):
        """Test that orders are deleted when customer is deleted"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        order_id = order.id
        self.customer.delete()
        
        # Order should be deleted due to CASCADE
        self.assertFalse(Order.objects.filter(id=order_id).exists())
    
    def test_order_cascade_delete_with_shop(self):
        """Test that orders are deleted when shop is deleted"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        order_id = order.id
        self.shop.delete()
        
        # Order should be deleted due to CASCADE
        self.assertFalse(Order.objects.filter(id=order_id).exists())


class OrderItemModelTest(TestCase):
    """Comprehensive unit tests for the OrderItem model"""
    
    def setUp(self):
        """Set up test data for each test method"""
        # Create test users
        self.customer = User.objects.create_user(
            username='testcustomer2',
            email='customer2@test.com',
            password='testpass123',
            phone='555-0200'
        )
        
        self.shop_owner = User.objects.create_user(
            username='shopowner2',
            email='owner2@test.com',
            password='testpass123',
            phone='555-0201'
        )
        
        # Create test shop
        self.shop = Shop.objects.create(
            owner=self.shop_owner,
            name='Test Dry Cleaners',
            address='123 Test Street, Test City',
            phone='555-0123'
        )
        
        # Create test service
        self.service = Service.objects.create(
            shop=self.shop,
            name='Dry Clean',
            description='Professional dry cleaning service'
        )
        
        # Create test item
        self.item = Item.objects.create(
            shop=self.shop,
            name='Shirt',
            description='Dress shirt'
        )
        
        # Create test service price
        self.service_price = ServicePrice.objects.create(
            shop=self.shop,
            service=self.service,
            item=self.item,
            price=Decimal('15.99')
        )
        
        # Create test order
        self.order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
    
    def test_order_item_creation_with_valid_data(self):
        """Test creating an order item with valid data"""
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=2,
            unit_price=Decimal('15.99')
        )
        
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.service_price, self.service_price)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal('15.99'))
        self.assertEqual(order_item.total_price, Decimal('31.98'))  # 15.99 * 2
    
    def test_order_item_unit_price_auto_population(self):
        """Test that unit_price is automatically set from service_price if not provided"""
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=1
        )
        
        # unit_price should be automatically set from service_price
        self.assertEqual(order_item.unit_price, self.service_price.price)
    
    def test_order_item_total_price_calculation(self):
        """Test that total_price is calculated correctly"""
        test_cases = [
            (1, Decimal('15.99'), Decimal('15.99')),
            (3, Decimal('10.00'), Decimal('30.00')),
            (5, Decimal('7.50'), Decimal('37.50')),
        ]
        
        for quantity, unit_price, expected_total in test_cases:
            with self.subTest(quantity=quantity, unit_price=unit_price):
                order_item = OrderItem.objects.create(
                    order=self.order,
                    service_price=self.service_price,
                    quantity=quantity,
                    unit_price=unit_price
                )
                self.assertEqual(order_item.total_price, expected_total)
    
    def test_order_item_with_notes(self):
        """Test creating order item with notes"""
        notes = 'Extra starch, gentle cycle'
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=1,
            unit_price=Decimal('15.99'),
            notes=notes
        )
        
        self.assertEqual(order_item.notes, notes)
    
    def test_order_item_triggers_order_total_calculation(self):
        """Test that saving an order item triggers order total recalculation"""
        # Initial order should have zero totals
        self.assertEqual(self.order.subtotal, Decimal('0.00'))
        self.assertEqual(self.order.total_amount, Decimal('0.00'))
        
        # Create first order item
        OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=2,
            unit_price=Decimal('15.99')
        )
        
        # Order totals should be updated
        self.order.refresh_from_db()
        expected_subtotal = Decimal('31.98')
        expected_total = expected_subtotal
        
        self.assertEqual(self.order.subtotal, expected_subtotal)
        self.assertEqual(self.order.total_amount, expected_total)
    
    def test_order_item_string_representation(self):
        """Test the __str__ method of OrderItem model"""
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=3,
            unit_price=Decimal('15.99')
        )
        
        expected_str = f"{self.service.name} + {self.item.name} x3"
        self.assertEqual(str(order_item), expected_str)
    
    def test_order_item_cascade_delete_with_order(self):
        """Test that order items are deleted when order is deleted"""
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=1,
            unit_price=Decimal('15.99')
        )
        
        order_item_id = order_item.id
        self.order.delete()
        
        # Order item should be deleted due to CASCADE
        self.assertFalse(OrderItem.objects.filter(id=order_item_id).exists())
    
    def test_order_item_cascade_delete_with_service_price(self):
        """Test that order items are deleted when service_price is deleted"""
        order_item = OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=1,
            unit_price=Decimal('15.99')
        )
        
        order_item_id = order_item.id
        self.service_price.delete()
        
        # Order item should be deleted due to CASCADE
        self.assertFalse(OrderItem.objects.filter(id=order_item_id).exists())
    
    def test_order_item_quantity_validation(self):
        """Test that quantity must be positive"""
        # Test with zero quantity - should be invalid
        order_item = OrderItem(
            order=self.order,
            service_price=self.service_price,
            quantity=0,
            unit_price=Decimal('15.99')
        )
        
        with self.assertRaises(ValidationError):
            order_item.full_clean()
    
    def test_multiple_order_items_total_calculation(self):
        """Test order total calculation with multiple items"""
        # Create multiple order items
        OrderItem.objects.create(
            order=self.order,
            service_price=self.service_price,
            quantity=2,
            unit_price=Decimal('15.99')
        )
        
        # Create another service price for different item
        pants = Item.objects.create(
            shop=self.shop,
            name='Pants',
            description='Dress pants'
        )
        
        pants_service_price = ServicePrice.objects.create(
            shop=self.shop,
            service=self.service,
            item=pants,
            price=Decimal('18.50')
        )
        
        OrderItem.objects.create(
            order=self.order,
            service_price=pants_service_price,
            quantity=1,
            unit_price=Decimal('18.50')
        )
        
        # Check final order totals
        self.order.refresh_from_db()
        expected_subtotal = Decimal('50.48')  # (15.99 * 2) + 18.50
        expected_total = expected_subtotal
        
        self.assertEqual(self.order.subtotal, expected_subtotal)
        self.assertEqual(self.order.total_amount, expected_total)


class OrderStatusHistoryModelTest(TestCase):
    """Unit tests for the OrderStatusHistory model"""
    
    def setUp(self):
        """Set up test data for each test method"""
        # Create test users
        self.customer = User.objects.create_user(
            username='testcustomer3',
            email='customer3@test.com',
            password='testpass123',
            phone='555-0300'
        )
        
        self.shop_owner = User.objects.create_user(
            username='shopowner3',
            email='owner3@test.com',
            password='testpass123',
            phone='555-0301'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff3',
            email='staff3@test.com',
            password='testpass123',
            phone='555-0302'
        )
        
        # Create test shop
        self.shop = Shop.objects.create(
            owner=self.shop_owner,
            name='Test Dry Cleaners',
            address='123 Test Street, Test City',
            phone='555-0123'
        )
        
        # Create test order
        self.order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            order_number='TEST123'
        )
    
    def test_order_status_history_creation(self):
        """Test creating order status history entry"""
        notes = 'Order confirmed by staff'
        history = OrderStatusHistory.objects.create(
            order=self.order,
            status='confirmed',
            changed_by=self.staff_user,
            notes=notes
        )
        
        self.assertEqual(history.order, self.order)
        self.assertEqual(history.status, 'confirmed')
        self.assertEqual(history.changed_by, self.staff_user)
        self.assertEqual(history.notes, notes)
        self.assertIsNotNone(history.changed_at)
    
    def test_order_status_history_string_representation(self):
        """Test the __str__ method of OrderStatusHistory model"""
        history = OrderStatusHistory.objects.create(
            order=self.order,
            status='in_progress',
            changed_by=self.staff_user
        )
        
        expected_str = 'Order #TEST123 -> in_progress'
        self.assertEqual(str(history), expected_str)
    
    def test_order_status_history_ordering(self):
        """Test that status history is ordered by changed_at descending"""
        # Create multiple status changes
        history1 = OrderStatusHistory.objects.create(
            order=self.order,
            status='confirmed',
            changed_by=self.staff_user
        )
        
        import time
        time.sleep(0.01)
        
        history2 = OrderStatusHistory.objects.create(
            order=self.order,
            status='in_progress',
            changed_by=self.staff_user
        )
        
        history_entries = list(OrderStatusHistory.objects.all())
        self.assertEqual(history_entries[0], history2)  # Most recent first
        self.assertEqual(history_entries[1], history1)
    
    def test_order_status_history_cascade_delete(self):
        """Test that status history is deleted when order is deleted"""
        history = OrderStatusHistory.objects.create(
            order=self.order,
            status='confirmed',
            changed_by=self.staff_user
        )
        
        history_id = history.id
        self.order.delete()
        
        # History should be deleted due to CASCADE
        self.assertFalse(OrderStatusHistory.objects.filter(id=history_id).exists())


class OrderModelEdgeCasesTest(TestCase):
    """Test edge cases and error scenarios for Order and OrderItem models"""
    
    def setUp(self):
        """Set up test data for each test method"""
        # Create minimal test data
        self.customer = User.objects.create_user(
            username='testcustomer4',
            email='customer4@test.com',
            password='testpass123',
            phone='555-0400'
        )
        
        self.shop_owner = User.objects.create_user(
            username='shopowner4',
            email='owner4@test.com',
            password='testpass123',
            phone='555-0401'
        )
        
        self.shop = Shop.objects.create(
            owner=self.shop_owner,
            name='Test Dry Cleaners',
            address='123 Test Street, Test City',
            phone='555-0123'
        )
    
    def test_order_with_empty_customer_name(self):
        """Test order creation with empty customer name"""
        # This should be allowed by model but might be validated at form level
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='',
            customer_phone='555-0456'
        )
        
        self.assertEqual(order.customer_name, '')
    
    def test_order_with_empty_customer_phone(self):
        """Test order creation with empty customer phone"""
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone=''
        )
        
        self.assertEqual(order.customer_phone, '')
    
    def test_order_with_very_long_special_instructions(self):
        """Test order with very long special instructions"""
        long_instructions = 'Very long instructions ' * 100  # Very long text
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            special_instructions=long_instructions
        )
        
        self.assertEqual(order.special_instructions, long_instructions)
    
    def test_order_duplicate_order_number_constraint(self):
        """Test that duplicate order numbers raise IntegrityError"""
        Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456',
            order_number='DUPLICATE123'
        )
        
        with self.assertRaises(IntegrityError):
            Order.objects.create(
                customer=self.customer,
                shop=self.shop,
                customer_name='Jane Doe',
                customer_phone='555-0789',
                order_number='DUPLICATE123'
            )
    
    @patch('time.time')
    @patch('random.randint')
    def test_order_number_generation_with_mocked_time(self, mock_random, mock_time):
        """Test order number generation with mocked timestamp"""
        mock_time.return_value = 1234567890.123456
        mock_random.return_value = 42
        
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        # Expected: shop_id + last 10 digits of timestamp + random suffix
        timestamp_part = str(int(1234567890.123456 * 1000000))[-10:]
        expected_order_number = f"{self.shop.id}{timestamp_part}42"
        self.assertEqual(order.order_number, expected_order_number)
    
    def test_order_calculate_total_with_precision(self):
        """Test decimal precision in total calculations"""
        # Create test data
        service = Service.objects.create(
            shop=self.shop,
            name='Test Service'
        )
        
        item = Item.objects.create(
            shop=self.shop,
            name='Test Item'
        )
        
        service_price = ServicePrice.objects.create(
            shop=self.shop,
            service=service,
            item=item,
            price=Decimal('10.333')  # Price with more than 2 decimal places
        )
        
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop,
            customer_name='John Doe',
            customer_phone='555-0456'
        )
        
        OrderItem.objects.create(
            order=order,
            service_price=service_price,
            quantity=3,
            unit_price=Decimal('10.33')  # Rounded to 2 decimal places
        )
        
        order.refresh_from_db()
        self.assertEqual(order.subtotal, Decimal('30.99'))
        self.assertEqual(order.total_amount, Decimal('30.99'))
