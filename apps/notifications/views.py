from typing import Any

import redis.asyncio as aioredis
from django.conf import settings
from django.db.models import QuerySet
from django.http.response import StreamingHttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.blog.pagination import DefaultPagination

from .models import Notification
from .serializers import NotificationSerializer

import asyncio
import logging

logger = logging.getLogger("notifications")

SSE_CHANNEL = "post_published"

@extend_schema(
    summary="Live post publication stream (SSE)",
    description=(
        "Server-Sent Events stream. Returns text/event-stream — "
        "connection stays open, server pushes events when a post is published. "
        "No authentication required. "
        "SSE is chosen over WebSocket because data flows only server→client."
    ),
    responses={
        200: OpenApiResponse(
            description="SSE stream — each event contains post_id, title, slug, author, published_at",
        )
    },
    tags=["Posts"],
)
async def post_stream_view(request: Any) -> StreamingHttpResponse:
    """
    GET /api/posts/stream/
    """

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
            await redis_client.aclose()

    response = StreamingHttpResponse(
        event_stream(), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


class NotificationViewSet(viewsets.GenericViewSet):
    """
    list  — GET  /api/notifications/        
    count — GET  /api/notifications/count/  
    read  — POST /api/notifications/read/   
    """

    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = DefaultPagination

    def get_queryset(self) -> QuerySet[Notification]:
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("comment", "comment__post")
            .order_by("-created_at")
        )

    def get_permissions(self) -> list:
        return [permission() for permission in self.permission_classes]

    @extend_schema(
        summary="List notifications",
        responses={200: NotificationSerializer(many=True)},
        tags=["Notifications"],
    )
    def list(self, request: Request) -> Response:
        logger.info("Notification list requested by user_id=%s", request.user.id)
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Unread notification count",
        responses={200: OpenApiResponse(description="Unread count")},
        tags=["Notifications"],
    )
    @action(detail=False, methods=("get",), url_path="count")
    def count(self, request: Request) -> Response:
        unread_count: int = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        logger.info("Unread count=%s for user_id=%s", unread_count, request.user.id)
        return Response({"unread_count": unread_count})

    @extend_schema(
        summary="Mark all notifications as read",
        request=None,
        responses={200: OpenApiResponse(description="Marked read count")},
        tags=["Notifications"],
    )
    @action(detail=False, methods=("post",), url_path="read")
    def read(self, request: Request) -> Response:
        logger.info("Mark all notifications read for user_id=%s", request.user.id)
        updated: int = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        logger.info(
            "Marked %s notifications as read for user_id=%s",
            updated,
            request.user.id,
        )
        return Response({"marked_read": updated}, status=status.HTTP_200_OK)