import json
import logging
from typing import Any, Mapping

import redis
from django.conf import settings

logger = logging.getLogger("blog")

SSE_CHANNEL = "post_published"
COMMENTS_CHANNEL = "comments"


def publish_post_published(post: Any) -> None:
    try:
        r = redis.from_url(settings.REDIS_URL)
        payload = json.dumps(
            {
                "post_id": post.id,
                "title": post.title,
                "slug": post.slug,
                "author": {
                    "id": post.author.id,
                    "email": post.author.email,
                },
                "published_at": post.updated_at.isoformat(),
            }
        )
        r.publish(SSE_CHANNEL, payload)
        logger.info("SSE event published for post_id=%s", post.id)
    except Exception:
        logger.exception("Failed to publish SSE event for post_id=%s", post.id)


def publish_comment_created(payload: Mapping[str, Any]) -> None:
    """Publish to Redis pub/sub (channel matches listen_comments management command)."""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.publish(COMMENTS_CHANNEL, json.dumps(dict(payload)))
        logger.debug("Published comment_created to channel=%s", COMMENTS_CHANNEL)
    except Exception:
        logger.exception("Failed to publish comment_created event")
