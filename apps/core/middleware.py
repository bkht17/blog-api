from django.utils.translation import get_language_from_request
from django.utils import timezone, translation
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.users.constants import SUPPORTED_LANGUAGE_CODES, LANGUAGE_EN


class LanguageTimezoneMiddleware:
    """
    Middleware that resolves the active language and timezone for each request

    Language priority:
    1. Authenticated user's preferred lang
    2. ?lang= query parameter
    3. Accept-Language HTTP header
    4. Default language(settings.LANGUAGE_CODE)

    Timzone:
    - Authenticated users use their saved timezone
    - Anonymous users use UTC
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = None
        user = None

        try:
            jwt_auth = JWTAuthentication()
            result = jwt_auth.authenticate(request)
            if result is not None:
                user, _ = result
        except Exception:
            pass

        # User profile lang
        if user is not None:
            user_language = getattr(user, "preferred_language", None)
            if user_language in SUPPORTED_LANGUAGE_CODES:
                language = user_language

        # Query param
        if not language:
            lang_param = request.GET.get("lang")
            if lang_param in SUPPORTED_LANGUAGE_CODES:
                language = lang_param

        # Accept-Language header
        if not language:
            header_lang = get_language_from_request(request)
            if header_lang in SUPPORTED_LANGUAGE_CODES:
                language = header_lang

        # Default
        if not language:
            language = LANGUAGE_EN

        translation.activate(language)
        request.LANGUAGE_CODE = language

        # Timezone activation
        if request.user.is_authenticated:
            user_timezone = getattr(request.user, "timezone", None)
            if user_timezone:
                try:
                    timezone.activate(user_timezone)
                except Exception:
                    timezone.activate("UTC")
            else:
                timezone.activate("UTC")
        else:
            timezone.activate("UTC")

        response = self.get_response(request)
        response["Content-Language"] = language
        return response
