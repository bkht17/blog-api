from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    response = exception_handler(exc, context)

    # Throttling can come from DRR or our rate-limit integration
    if response is not None and response.status_code == 429:
        response.data = {"detail": "Too many requests. Try again later."}

    return response
