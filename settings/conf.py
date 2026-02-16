from decouple import config

ENV_ID = config('BLOG_ENV_ID', default='local')
SECRET_KEY = config('BLOG_SECRET_KEY', default='your-secret-key')
DEBUG = config('BLOG_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('BLOG_ALLOWED_HOSTS', default='localhost,127.0.1', cast=lambda v: [s.strip() for s in v.split(',')])