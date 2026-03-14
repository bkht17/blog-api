import asyncio
import httpx

from django.http import JsonResponse
from django.views import View
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.blog.models import Post, Comment, PostStatus
from apps.users.models import User


async def _fetch_exchange_rates() -> dict:
    """
    Async HTTP call to open.er-api.com.
    We use async here because this is an I/O-bound network call.
    If this were sync, it would block the entire Django worker thread
    while waiting for the external API response.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://open.er-api.com/v6/latest/USD")
        resp.raise_for_status()
        rates = resp.json().get("rates", {})
        return {
            "KZT": rates.get("KZT"),
            "RUB": rates.get("RUB"),
            "EUR": rates.get("EUR"),
        }


async def _fetch_current_time() -> str:
    """
    Async HTTP call to timeapi.io.
    Same reasoning — pure network I/O, should not block the worker thread.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://timeapi.io/api/time/current/zone",
            params={"timeZone": "Asia/Almaty"},
        )
        resp.raise_for_status()
        return resp.json().get("dateTime", now().isoformat())


class StatsView(View):
    """
    Async Django View — DRF does not support async views natively,
    so we use a plain Django View.
    asyncio.gather fires both external HTTP calls concurrently:
    total latency = max(t_rates, t_time), not t_rates + t_time.
    """

    async def get(self, request, *args, **kwargs):
        total_posts = await Post.objects.filter(status=PostStatus.PUBLISHED).acount()
        total_comments = await Comment.objects.acount()
        total_users = await User.objects.acount()

        exchange_rates, current_time = await asyncio.gather(
            _fetch_exchange_rates(),
            _fetch_current_time(),
        )

        return JsonResponse(
            {
                "blog": {
                    "total_posts": total_posts,
                    "total_comments": total_comments,
                    "total_users": total_users,
                },
                "exchange_rates": exchange_rates,
                "current_time": current_time,
            }
        )


# stats_view — ready-to-use in urls.py with Swagger docs attached
stats_view = extend_schema(
    summary="Blog Statistics",
    description=(
        "Returns blog statistics (posts, comments, users) combined with "
        "live exchange rates and current Almaty time. "
        "The two external API calls are made concurrently via asyncio.gather, "
        "so total response time equals the slowest of the two calls, not their sum. "
        "No authentication required."
    ),
    responses={
        200: OpenApiResponse(
            description="Stats",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "blog": {
                            "total_posts": 42,
                            "total_comments": 137,
                            "total_users": 15,
                        },
                        "exchange_rates": {"KZT": 450.23, "RUB": 89.10, "EUR": 0.92},
                        "current_time": "2024-03-15T18:30:00+05:00",
                    },
                )
            ],
        )
    },
    tags=["Stats"],
)(StatsView.as_view())
