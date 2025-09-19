from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

from .serializers import RegisterSerializer, UserSerializer, LoginResponseSerializer

logger = logging.getLogger(__name__)

User = get_user_model()

# Register User
@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='post')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(f'New user registered: {user.username} from IP: {self.get_client_ip()}')
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

# Login with JWT
# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = LoginResponseSerializer

#     def post(self, request, *args, **kwargs):
#         response = super().post(request, *args, **kwargs)
#         if response.status_code == 200:
#             user = User.objects.get(username=request.data['username'])
#             refresh = RefreshToken.for_user(user)
#             data = {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#                 "user": UserSerializer(user).data
#             }
#             return Response(data, status=status.HTTP_200_OK)
#         return response

@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            data = response.data
            data["user"] = UserSerializer(user).data
            logger.info(f'Successful login: {user.username} from IP: {self.get_client_ip()}')
            return Response(data, status=200)
        else:
            logger.warning(f'Failed login attempt for username: {request.data.get("username", "unknown")} from IP: {self.get_client_ip()}')
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

# Profile
class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
