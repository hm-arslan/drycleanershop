import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all API requests for security monitoring
    """
    def process_request(self, request):
        # Log API requests
        if request.path.startswith('/api/'):
            client_ip = self.get_client_ip(request)
            user = request.user if request.user.is_authenticated else 'Anonymous'
            logger.info(
                f"API Request: {request.method} {request.path} "
                f"from {client_ip} by {user}"
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AccountLockoutMiddleware(MiddlewareMixin):
    """
    Handle account lockout after failed login attempts
    """
    def process_request(self, request):
        if request.path == '/api/auth/login/' and request.method == 'POST':
            username = request.POST.get('username') or request.data.get('username')
            if username:
                try:
                    user = User.objects.get(username=username)
                    
                    # Check if account is currently locked
                    if (user.account_locked_until and 
                        user.account_locked_until > timezone.now()):
                        return JsonResponse({
                            'error': 'Account is temporarily locked due to multiple failed login attempts. '
                                   'Please try again later.'
                        }, status=423)
                        
                except User.DoesNotExist:
                    # Don't reveal if user exists or not
                    pass
        
        return None


class IPBanMiddleware(MiddlewareMixin):
    """
    Simple IP-based rate limiting and banning
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.failed_attempts = {}  # In production, use Redis or database
        super().__init__(get_response)
    
    def process_request(self, request):
        client_ip = self.get_client_ip(request)
        
        # Check if IP has too many failed attempts
        if client_ip in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[client_ip]
            
            # Reset counter if it's been more than 1 hour
            if timezone.now() - last_attempt > timedelta(hours=1):
                del self.failed_attempts[client_ip]
            elif attempts >= 20:  # Ban after 20 failed attempts
                logger.warning(f"IP {client_ip} has been temporarily banned due to excessive requests")
                return JsonResponse({
                    'error': 'Too many requests. Please try again later.'
                }, status=429)
        
        return None
    
    def process_response(self, request, response):
        # Track failed login attempts
        if (request.path == '/api/auth/login/' and 
            request.method == 'POST' and 
            response.status_code == 400):
            
            client_ip = self.get_client_ip(request)
            if client_ip in self.failed_attempts:
                attempts, _ = self.failed_attempts[client_ip]
                self.failed_attempts[client_ip] = (attempts + 1, timezone.now())
            else:
                self.failed_attempts[client_ip] = (1, timezone.now())
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip