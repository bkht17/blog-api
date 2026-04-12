from datetime import timedelta
from typing import Any

from celery import shared_task
from django.utils import timezone

import logging

logger = logging.getLogger("blog")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_posts_cache(self: Any) -> None:
    from django.core.cache import cache

    from apps.users.constants import SUPPORTED_LANGUAGE_CODES
    from apps.blog.constants import PUBLISHED_POSTS_LIST_CACHE_KEY_PREFIX

    for language_code in SUPPORTED_LANGUAGE_CODES:
        cache_key = f"{PUBLISHED_POSTS_LIST_CACHE_KEY_PREFIX}:{language_code}"
        cache.delete(cache_key)

    logger.info("Posts cache invalidated")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def publish_scheduled_posts(self: Any) -> None:
    from apps.blog.models import Post, PostStatus
    from apps.blog.redis_pubsub import publish_post_published

    due_posts = Post.objects.filter(
        status=PostStatus.SCHEDULED,
        publish_at__lte=timezone.now(),
    ).select_related("author")

    count: int = 0
    for post in due_posts:
        post.status = PostStatus.PUBLISHED
        post.save(update_fields=("status", "updated_at"))
        publish_post_published(post)
        count += 1
        logger.info("Auto-published post: id=%s slug=%s", post.id, post.slug)

    if count:
        logger.info("publish_scheduled_posts: published %d posts", count)


@shared_task
def generate_daily_stats() -> None:
    from django.contrib.auth import get_user_model

    from apps.blog.models import Comment, Post

    User = get_user_model()
    since = timezone.now() - timedelta(hours=24)

    posts_count: int = Post.objects.filter(created_at__gte=since).count()
    comments_count: int = Comment.objects.filter(created_at__gte=since).count()
    users_count: int = User.objects.filter(date_joined__gte=since).count()

    logger.info(
        "Daily stats — posts: %d, comments: %d, new users: %d",
        posts_count,
        comments_count,
        users_count,
    )
