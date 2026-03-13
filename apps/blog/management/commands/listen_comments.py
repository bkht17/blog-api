import asyncio
import json

from django.core.management.base import BaseCommand
from django.conf import settings
from urllib.parse import urlparse

from redis.asyncio import Redis

class Command(BaseCommand):
    help = "Subscribe to Redis 'comments' channel and print incoming messages."

    def handle(self, *args, **options):
        asyncio.run(self._listen())
    
    async def _listen(self):
        url = urlparse(settings.REDIS_URL)
        db = int((url.path or "/0").lstrip("/"))
        client = Redis(
            host=url.hostname or "127.0.0.1",
            port=url.port or 6379,
            db=db,
            password=url.password,
            decode_responses=True,
        )
        
        pubsub = client.pubsub()
        await pubsub.subscribe("comments")
        self.stdout.write(self.style.SUCCESS("Listening to Redis channel: comments"))
        
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            
            raw = message.get("data", "")
            try:
                event = json.loads(raw)
                self.stdout.write(
                    f"[comment_created] post={event.get('post_slug')}"
                    f" author_id={event.get('author_id')}"
                    f"body={event.get('body', '')[:80]}"
                )
            except (json.JSONDecodeError, AttributeError):
                self.stdout.write(f"Raw message: {raw}")