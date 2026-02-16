from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import QuerySet

from .models import *
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly
from .pagination import DefaultPagination

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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, slug=None):
        post = self.get_object()
        if request.method == 'GET':
            qs = Comment.objects.filter(post=post).select_related('author').order_by('-created_at')
            page = self.paginate_queryset(qs)
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        #POST
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
                
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            body=serializer.validated_data['body']
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)