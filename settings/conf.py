from decouple import config

ENV_ID = config('BLOG_ENV_ID', default='local')
SECRET_KEY = config('BLOG_SECRET_KEY', default='your-secret-key')
DEBUG = config('BLOG_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('BLOG_ALLOWED_HOSTS', default='localhost,127.0.1', cast=lambda v: [s.strip() for s in v.split(',')])
REDIS_URL = config('BLOG_REDIS_URL', default='redis://127.0.0.1:6379/1')