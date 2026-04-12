import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

logger = logging.getLogger("notifications")
User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"post_{self.slug}_comments"
        
        print(f"New WebSocket connection for post: {self.slug}")

        print(f"qs raw: {self.scope.get('query_string')}")
        user = await self._authenticate()
        print(f"Authenticated user: {user}")
        if user is None:
            print("Authentication failed, closing connection")
            await self.close(code=4001)
            return

        if not await self._post_exists(self.slug):
            print("Post does not exist, closing connection")
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket connection accepted for post: {self.slug}")

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def comment_created(self, event: dict) -> None:
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def _authenticate(self):
        from urllib.parse import parse_qs
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])
        if not token_list:
            return None
        try:
            token = AccessToken(token_list[0])
            return User.objects.get(id=token["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def _post_exists(self, slug: str) -> bool:
        from apps.blog.models import Post
        return Post.objects.filter(slug=slug).exists()
