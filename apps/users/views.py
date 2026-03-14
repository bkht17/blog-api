from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UserLanguageSerializer,
    UserTimezoneSerializer,
)
from .emails import send_welcome_email

import logging

logger = logging.getLogger("users")


# Create your views here.
class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Registration",
        description="Allows new users to register by providing their email, first name, last name, and password.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully.",
            ),
            400: OpenApiResponse(
                description="Invalid input data.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
        examples=[
            OpenApiExample(
                "User Registration",
                value={
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "password": "securepassword",
                    "password2": "securepassword",
                    "preferred_language": "en",
                    "timezone": "UTC",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register response example",
                value={
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "preferred_language": "en",
                        "timezone": "UTC",
                    },
                    "tokens": {"refresh": "refresh_token", "access": "access_token"},
                },
                response_only=True,
                status_codes=[201],
            ),
        ],
        tags=["Auth"],
    )
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True, method="POST"))
    def create(self, request):
        logger.info("Registration attempt for email: %s", request.data.get("email"))
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
            send_welcome_email(user)
        except Exception:
            logger.exception(
                "Error occurred during registration for email: %s",
                request.data.get("email"),
            )
            raise

        logger.info("User registered successfully: %s", user.email)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoggingTokenObtainPairView(TokenObtainPairView):
    @method_decorator(ratelimit(key="ip", rate="10/m", block=True, method="POST"))
    def post(self, request, *args, **kwargs):
        logger.info("Login attempt for email: %s", request.data.get("email"))

        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            logger.exception(
                "Error occurred during login for email: %s", request.data.get("email")
            )
            raise

        if response.status_code == status.HTTP_200_OK:
            logger.info("Login successful for email: %s", request.data.get("email"))
        else:
            logger.warning(
                "Login failed for email: %s status=%s",
                request.data.get("email"),
                response.status_code,
            )
        return response


class UserPreferenceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    @extend_schema(
        summary="Update Preferred Language",
        description="Allows authenticated users to update their preferred language.",
        request=UserLanguageSerializer,
        responses={
            200: OpenApiResponse(
                description="Preferred language updated successfully.",
            ),
            400: OpenApiResponse(
                description="Invalid input data.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
        examples=[
            OpenApiExample(
                "Update Preferred Language",
                value={"preferred_language": "en"},
                request_only=True,
            ),
        ],
        tags=["Auth"],
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="language",
    )
    def language(self, request):
        serializer = UserLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.preferred_language = serializer.validated_data[
            "preferred_language"
        ]
        request.user.save(update_fields=["preferred_language"])

        return Response(
            {
                "detail": _("Preferred language updated successfully."),
                "preferred_language": request.user.preferred_language,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Update Timezone",
        description="Allows authenticated users to update their timezone.",
        request=UserTimezoneSerializer,
        responses={
            200: OpenApiResponse(
                description="Timezone updated successfully.",
            ),
            400: OpenApiResponse(
                description="Invalid input data.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
        examples=[
            OpenApiExample(
                "Update Timezone",
                value={"timezone": "UTC"},
                request_only=True,
            ),
        ],
        tags=["Auth"],
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="timezone",
    )
    def timezone(self, request):
        serializer = UserTimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])

        return Response(
            {
                "detail": _("Timezone updated successfully."),
                "timezone": request.user.timezone,
            },
            status=status.HTTP_200_OK,
        )
