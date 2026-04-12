from decouple import config

SECRET_KEY = config("BLOG_SECRET_KEY")
DEBUG = config("BLOG_DEBUG", default=True, cast=bool)
REDIS_URL = config("BLOG_REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = config(
    "BLOG_CELERY_BROKER_URL", default="redis://localhost:6379/1"
)
FLOWER_USER = config("BLOG_FLOWER_USER", default="admin")
FLOWER_PASSWORD = config("BLOG_FLOWER_PASSWORD", default="changeme")
SEED_DB = config("BLOG_SEED_DB", default=False, cast=bool)
