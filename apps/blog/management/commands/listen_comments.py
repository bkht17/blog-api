import redis
from django.core.management.base import BaseCommand
from django.conf import settings
from urllib.parse import urlparse


class Command(BaseCommand):
    help = "Subscribe to Redis 'comments' channel and print incoming messages."

    def handle(self, *args, **options):
        url = urlparse(settings.REDIS_URL)
        db = int((url.path or "/0").lstrip("/"))
        client = redis.Redis(
            host=url.hostname or "127.0.0.1",
            port=url.port or 6379,
            db=db,
            password=url.password,
            decode_responses=True,
        )

        pubsub = client.pubsub()
        pubsub.subscribe("comments")

        self.stdout.write(self.style.SUCCESS("Listening to Redis channel: comments"))

        for message in pubsub.listen():
            # message types: subscribe, message, etc.
            if message.get("type") != "message":
                continue
            self.stdout.write(message.get("data"))