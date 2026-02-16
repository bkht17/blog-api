from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import QuerySet
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .constants import PUBLISHED_POSTS_LIST_CACHE_KEY, PUBLISHED_POSTS_LIST_CACHE_TTL_SECONDS
from .models import *
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly
from .pagination import DefaultPagination
from .redis_pubsub import publist_comment_created

import logging

logger = logging.getLogger("blog")

# Create your views here.
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    pagination_class = DefaultPagination
    lookup_field = 'slug'
    
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.AllowAny]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
    
    def get_queryset(self) -> QuerySet[Post]:
        qs = Post.objects.select_related('author', 'category').prefetch_related('tags')
        if self.action in ('list', 'retrieve'):
            return qs.filter(status='published')
        return qs

    def perform_create(self, serializer: PostSerializer) -> None:
        logger.info("Post create attempt by user: %s", self.request.user.id)
        post = serializer.save(author=self.request.user)
        cache.delete(PUBLISHED_POSTS_LIST_CACHE_KEY)
        logger.info("Post created successfully: id=%s, slug=%s, author_id=%s", post.id, post.slug, post.author_id)
        
    def perform_update(self, serializer: PostSerializer) -> None:
        post = self.get_object()
        logger.info("Post update attempt: id=%s slug=%s by user: %s", post.id, post.slug, self.request.user.id)
        serializer.save()
        cache.delete(PUBLISHED_POSTS_LIST_CACHE_KEY)
        logger.info("Post updated successfully: id=%s slug=%s", post.id, post.slug)
        
    def perform_destroy(self, instance: Post) -> None:
        logger.info("Post delete attempt: id=%s slug=%s by user: %s", instance.id, instance.slug, self.request.user.id)
        instance.delete()
        logger.info("Post deleted successfully: id=%s slug=%s", instance.id, instance.slug)
        
    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, slug=None):
        post = self.get_object()
        if request.method == 'GET':
            qs = Comment.objects.filter(post=post).select_related('author').order_by('-created_at')
            page = self.paginate_queryset(qs)
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        #POST
        logger.info("Comments create attempt: post_slug=%s by user: %s", post.slug, request.user.id)
        
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
                
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                body=serializer.validated_data['body']
            )
        except Exception:
            logger.exception("Error occurred while creating comment: post_slug=%s by user: %s", post.slug, request.user.id)
            raise
        
        publish_comment_created({
            "event": "comment_created",
            "comment_id": comment.id,
            "post_id": comment.post_id,
            "post_slug": post.slug,
            "author_id": comment.author_id,
            "created_at": comment.created_at.isoformat(),
            "body": comment.body,
        })
        logger.info("Published comment_created event to redis: comment_id=%s", comment.id)
        
        logger.info("Comment created successfully: id=%s post_id=%s author_id=%s", comment.id, comment.post_id, comment.author_id)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        cached_data = cache.get(PUBLISHED_POSTS_LIST_CACHE_KEY)
        if cached_data is not None:
            logger.debug("Cache hit for published posts list")
            return Response(cached_data)
        
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset
        serializer = self.get_serializer(page, many=True)
        data = self.get_paginated_response(serializer.data).data
        cache.set(PUBLISHED_POSTS_LIST_CACHE_KEY, data, timeout=PUBLISHED_POSTS_LIST_CACHE_TTL_SECONDS)
        return Response(data)
    
    @method_decorator(ratelimit(key='ip', rate='20/m', block=True, method='POST'))
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)