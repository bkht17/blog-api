import json
from urllib.parse import urlparse

import redis
from django.conf import settings

def _redis_client() -> redis.Redis:
    url = urlparse(settings.REDIS_URL)
    db = int((url.path or '0').lstrip('/'))
    return redis.Redis(
        host=url.hostname or "127.0.0.1", 
        port=url.port or 6379,
        db=db,
        password=url.password,
        decode_responses=True
    )
    
def publist_comment_created(payload: dict):
    client = _redis_client()
    client.publish('comment_created', json.dumps(payload))