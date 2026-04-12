# Python modules
import logging
import asyncio
from redis.asyncio import aioredis

# Django modules
from django.http.response import StreamingHttpResponse
from django.conf import settings

# Django REST Framework
from rest_framework import viewsets
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_200_OK,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

# Project modules
from .models import Notification
from .serializers import NotificationSerializer

logger = logging.getLogger("notifications")

SSE_CHANNEL = "post_published"


async def post_stream_view(request):
    async def event_stream():
        redis_client = await aioredis.from_url(settings.REDIS_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(SSE_CHANNEL)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    yield f"data: {data}\n\n"
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(SSE_CHANNEL)
            await redis_client.close()

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = IsAuthenticated

    def get_permissions(self) -> list:
        return [permission() for permission in self.permission_classes]

    def list(self, request: DRFRequest) -> DRFResponse:
        logger.info("Listing notifications for user: %s", request.user.id)
        qs = (
            Notification.objects.filter(recipient=request.user)
            .select_related("comment", "comment__post")
            .order_by("-created_at")
        )

        from apps.blog.pagination import DefaultPagination

        paginator = DefaultPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="count")
    def count(self, request: DRFRequest) -> DRFResponse:
        unread_count: int = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        logger.info(
            "Unread notifications count for user %s: %d", request.user.id, unread_count
        )
        return DRFResponse({"unread_count": unread_count}, status=HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="read")
    def read(self, request: DRFRequest, pk: int) -> DRFResponse:
        logger.info(
            "Marking notification as read: id=%s for user: %s", pk, request.user.id
        )
        updated: int = Notification.objects.filter(
            id=pk, recipient=request.user, is_read=False
        ).update(is_read=True)
        logger.info(
            "Notifications marked as read: %d for notification id: %s and user: %s",
            updated,
            pk,
            request.user.id,
        )
        return DRFResponse(
            {"detail": "Notification marked as read."}, status=HTTP_200_OK
        )
