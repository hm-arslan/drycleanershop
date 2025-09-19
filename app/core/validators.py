import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_phone_number(value):
    """
    Validate phone number format.
    Accepts formats like: +1234567890, (123) 456-7890, 123-456-7890, 123.456.7890
    """
    phone_regex = re.compile(r'^(\+?1-?)?(\([2-9][0-9]{2}\)|[2-9][0-9]{2})-?[2-9][0-9]{2}-?[0-9]{4}$|^\+?[1-9]\d{1,14}$')
    if not phone_regex.match(value):
        raise ValidationError(
            _('Enter a valid phone number.'),
            code='invalid_phone'
        )


def validate_no_special_chars(value):
    """
    Validate that value contains only alphanumeric characters, spaces, and basic punctuation.
    """
    if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', value):
        raise ValidationError(
            _('Only alphanumeric characters, spaces, hyphens, periods, and underscores are allowed.'),
            code='invalid_characters'
        )


def validate_price(value):
    """
    Validate that price is positive and has at most 2 decimal places.
    """
    if value <= 0:
        raise ValidationError(
            _('Price must be greater than 0.'),
            code='invalid_price'
        )
    
    # Check decimal places
    decimal_places = str(value).split('.')[-1] if '.' in str(value) else ''
    if len(decimal_places) > 2:
        raise ValidationError(
            _('Price cannot have more than 2 decimal places.'),
            code='too_many_decimals'
        )


def validate_order_quantity(value):
    """
    Validate order quantity is positive and reasonable.
    """
    if value <= 0:
        raise ValidationError(
            _('Quantity must be greater than 0.'),
            code='invalid_quantity'
        )
    
    if value > 100:  # Reasonable limit for dry cleaning items
        raise ValidationError(
            _('Quantity cannot exceed 100 items per order.'),
            code='quantity_too_high'
        )


def validate_text_length(value, max_length=1000):
    """
    Validate text length to prevent extremely long inputs.
    """
    if len(value) > max_length:
        raise ValidationError(
            _('Text cannot exceed %(max_length)d characters.'),
            code='text_too_long',
            params={'max_length': max_length}
        )


def validate_safe_string(value):
    """
    Basic XSS prevention - check for common malicious patterns.
    """
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick=',
        r'onmouseover=',
        r'<iframe',
        r'<object',
        r'<embed'
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            raise ValidationError(
                _('Invalid content detected. Please remove any scripts or HTML tags.'),
                code='unsafe_content'
            )