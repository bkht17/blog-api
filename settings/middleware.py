import logging
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("debug_requests")


class DebugRequestLoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        logger.debug(
            "REQUEST %s %s ip=%s",
            request.method,
            request.get_full_path(),
            request.META.get("REMOTE_ADDR"),
        )
        return self.get_response(request)
