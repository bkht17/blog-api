from datetime import timedelta
from typing import Any

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

import logging

logger = logging.getLogger("notifications")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(self: Any, comment_id: int) -> None:
    from apps.blog.models import Comment
    from apps.notifications.models import Notification

    try:
        comment = Comment.objects.select_related("author", "post", "post__author").get(
            id=comment_id
        )
    except Comment.DoesNotExist:
        logger.warning("process_new_comment: comment_id=%s not found", comment_id)
        return

    # Notification
    if comment.author_id != comment.post.author_id:
        Notification.objects.create(
            recipient=comment.post.author,
            comment=comment,
        )
        logger.info(
            "Notification created for user_id=%s comment_id=%s",
            comment.post.author_id,
            comment_id,
        )

    # WebSocket push
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_{comment.post.slug}_comments",
        {
            "type": "comment_created",
            "data": {
                "comment_id": comment.id,
                "author": {
                    "id": comment.author.id,
                    "email": comment.author.email,
                },
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
            },
        },
    )
    logger.info("process_new_comment: done comment_id=%s", comment_id)


@shared_task
def clear_expired_notifications() -> None:
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info("clear_expired_notifications: deleted %d records", deleted)
