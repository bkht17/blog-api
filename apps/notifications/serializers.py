from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    comment_body = serializers.CharField(source="comment.body", read_only=True)
    post_slug = serializers.CharField(source="comment.post.slug", read_only=True)
    post_title = serializers.CharField(source="comment.post.title", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "comment_id",
            "comment_body",
            "post_slug",
            "post_title",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields
