from rest_framework import serializers
from .models import *

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")
        
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        
class PostSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(write_only=True, child=serializers.IntegerField(), required=False)
    
    class Meta:
        model = Post
        fields = (
            "id",
            "author_email",
            "title",
            "slug",
            "body",
            "category",
            "category_id",
            "tags",
            "tag_ids",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        
    def create(self, validated_data: dict) -> Post:
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', [])
        
        post = Post.objects.create(**validated_data)
        
        if category_id is not None:
            post.category_id = category_id
            post.save(update_fields=['category'])
            
        if tag_ids:
            post.tags.set(tag_ids)
            
        return post
    
    def update(self, instance: Post, validated_data: dict) -> Post:
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if category_id is not None:
            instance.category_id = category_id
            
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance
    
class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    
    class Meta:
        model = Comment
        fields = ("id", "post", "author_email", "body", "created_at")
        read_only_fields = ("created_at",)