from django.contrib.auth import get_user_model
from rest_framework import serializers
from .constants import SUPPORTED_LANGUAGE_CODES
from django.utils.translation import gettext_lazy as _
from zoneinfo import available_timezones

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "date_joined",
            "preferred_language",
            "timezone",
        ]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)

    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)

    preferred_language = serializers.ChoiceField(
        choices=sorted(SUPPORTED_LANGUAGE_CODES),
        default="en",
        required=False,
    )

    timezone = serializers.CharField(max_length=64, default="UTC", required=False)

    def validate_timezone(self, value: str) -> str:
        if value not in available_timezones():
            raise serializers.ValidationError(_("Invalid timezone."))
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserLanguageSerializer(serializers.Serializer):
    preferred_language = serializers.ChoiceField(
        choices=sorted(SUPPORTED_LANGUAGE_CODES),
    )


class UserTimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=64)

    def validate_timezone(self, value: str) -> str:
        if value not in available_timezones():
            raise serializers.ValidationError(_("Invalid timezone."))
        return value
