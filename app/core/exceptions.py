import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    and logs security-related errors.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log security-related exceptions
    if response is not None:
        request = context.get('request')
        user = getattr(request, 'user', None)
        client_ip = get_client_ip(request) if request else 'Unknown'
        
        # Log authentication/permission errors
        if response.status_code in [401, 403]:
            logger.warning(
                f"Security violation: {exc.__class__.__name__} - "
                f"Status: {response.status_code} - "
                f"User: {user} - "
                f"IP: {client_ip} - "
                f"Path: {getattr(request, 'path', 'Unknown')}"
            )
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data if isinstance(response.data, dict) else {'detail': response.data},
            'status_code': response.status_code,
        }
        
        # Don't expose sensitive information in production
        if hasattr(context.get('request'), 'user'):
            debug_mode = getattr(context['request'], 'debug', False)
            if not debug_mode and response.status_code == 500:
                custom_response_data['details'] = {'detail': 'Internal server error'}
        
        response.data = custom_response_data
    
    # Handle Django validation errors
    elif isinstance(exc, ValidationError):
        logger.error(f"Validation error: {exc}")
        response = Response(
            {
                'error': True,
                'message': 'Validation failed',
                'details': {'validation_errors': exc.messages},
                'status_code': status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle 404 errors
    elif isinstance(exc, Http404):
        response = Response(
            {
                'error': True,
                'message': 'Resource not found',
                'details': {'detail': 'The requested resource was not found.'},
                'status_code': status.HTTP_404_NOT_FOUND,
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle unexpected errors
    else:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                'error': True,
                'message': 'An unexpected error occurred',
                'details': {'detail': 'Please contact support if the problem persists.'},
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def get_client_ip(request):
    """Get the client's IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip