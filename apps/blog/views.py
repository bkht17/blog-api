from rest_framework import viewsets, permissions
from django.db.models import QuerySet

from .models import Post
from .serializers import PostSerializer
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
