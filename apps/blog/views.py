from typing import Any

from django.core.cache import cache
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .constants import (
    PUBLISHED_POSTS_LIST_CACHE_KEY_PREFIX,
    PUBLISHED_POSTS_LIST_CACHE_TTL_SECONDS,
)
from .models import Comment, Post, PostStatus
from .pagination import DefaultPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostSerializer
from .redis_pubsub import publish_comment_created, publish_post_published

from apps.users.constants import SUPPORTED_LANGUAGE_CODES
from apps.notifications.tasks import process_new_comment
from apps.blog.tasks import invalidate_posts_cache

import logging

logger = logging.getLogger("blog")


# Create your views here.
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = DefaultPagination
    lookup_field = "slug"

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self) -> QuerySet[Post]:
        qs = Post.objects.select_related("author", "category").prefetch_related("tags")
        if self.action in ("list", "retrieve"):
            return qs.filter(status=PostStatus.PUBLISHED)
        return qs

    def perform_create(self, serializer: PostSerializer) -> None:
        logger.info("Post create attempt by user: %s", self.request.user.id)
        post = serializer.save(author=self.request.user)
        invalidate_posts_cache.delay()
        logger.info(
            "Post created successfully: id=%s, slug=%s, author_id=%s",
            post.id,
            post.slug,
            post.author_id,
        )

    def perform_update(self, serializer: PostSerializer) -> None:
        old_status = self.get_object().status
        post = serializer.save()  
        invalidate_posts_cache.delay()
        if old_status != PostStatus.PUBLISHED and post.status == PostStatus.PUBLISHED:
            publish_post_published(post)
        logger.info("Post updated: id=%s slug=%s", post.id, post.slug)

    def perform_destroy(self, instance: Post) -> None:
        logger.info(
            "Post delete attempt: id=%s slug=%s by user: %s",
            instance.id,
            instance.slug,
            self.request.user.id,
        )
        instance.delete()
        invalidate_posts_cache.delay()
        logger.info(
            "Post deleted successfully: id=%s slug=%s", instance.id, instance.slug
        )

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request: Request, slug: str | None = None) -> Response:
        post = self.get_object()
        if request.method == "GET":
            qs = (
                Comment.objects.filter(post=post)
                .select_related("author")
                .order_by("-created_at")
            )
            page = self.paginate_queryset(qs)
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # POST
        logger.info(
            "Comments create attempt: post_slug=%s by user: %s",
            post.slug,
            request.user.id,
        )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = Comment.objects.create(
                post=post, author=request.user, body=serializer.validated_data["body"]
            )
        except Exception:
            logger.exception(
                "Error occurred while creating comment: post_slug=%s by user: %s",
                post.slug,
                request.user.id,
            )
            raise

        publish_comment_created(
            {
                "event": "comment_created",
                "comment_id": comment.id,
                "post_id": comment.post_id,
                "post_slug": post.slug,
                "author_id": comment.author_id,
                "created_at": comment.created_at.isoformat(),
                "body": comment.body,
            }
        )
        
        process_new_comment.delay(comment.id)
        
        logger.info("process_new_comment task dispatched: comment_id=%s", comment.id)
        
        logger.info(
            "Published comment_created event to redis: comment_id=%s", comment.id
        )

        logger.info(
            "Comment created successfully: id=%s post_id=%s author_id=%s",
            comment.id,
            comment.post_id,
            comment.author_id,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        language = get_language() or "en"
        cache_key = f"{PUBLISHED_POSTS_LIST_CACHE_KEY_PREFIX}:{language}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug("Cache hit for published posts list, language=%s", language)
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        cache.set(
            cache_key,
            data,
            timeout=PUBLISHED_POSTS_LIST_CACHE_TTL_SECONDS,
        )

        logger.debug("Cache set for published posts list, language=%s", language)
        return Response(data)

    @method_decorator(ratelimit(key="ip", rate="20/m", block=True, method="POST"))
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().create(request, *args, **kwargs)

    def _invalidate_posts_list_cache(self) -> None:
        for language_code in SUPPORTED_LANGUAGE_CODES:
            cache_key = f"{PUBLISHED_POSTS_LIST_CACHE_KEY_PREFIX}:{language_code}"
            cache.delete(cache_key)
