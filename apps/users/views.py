from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


from .serializers import UserSerializer, RegisterSerializer

import logging

logger = logging.getLogger("users")

# Create your views here.
class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/m', block=True, method='POST'))  
    def create(self, request):
        logger.info("Registration attempt for email: %s", request.data.get("email"))
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except Exception:
            logger.exception("Error occurred during registration for email: %s", request.data.get("email"))
            raise
        
        logger.info("User registered successfully: %s", user.email)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
        
class LoggingTokenObtainPairView(TokenObtainPairView):
    @method_decorator(ratelimit(key='ip', rate='10/m', block=True, method='POST'))
    def post(self, request, *args, **kwargs):
        logger.info("Login attempt for email: %s", request.data.get("email"))
        
        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            logger.exception("Error occurred during login for email: %s", request.data.get("email"))
            raise
        
        if response.status_code == status.HTTP_200_OK:
            logger.info("Login successful for email: %s", request.data.get("email"))
        else:
            logger.warning("Login failed for email: %s status=%s", request.data.get("email"), response.status_code)
        return response
