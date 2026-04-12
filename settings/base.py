import os
from pathlib import Path

from .conf import REDIS_URL, SECRET_KEY, DEBUG, CELERY_BROKER_URL

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)
REDIS_URL = REDIS_URL

SECRET_KEY = SECRET_KEY
DEBUG = DEBUG
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.users",
    "apps.blog",
    "apps.core",
    "drf_spectacular",
    "channels",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "settings.middleware.DebugRequestLoggingMiddleware",
    "apps.core.middleware.LanguageTimezoneMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.blog.pagination.DefaultPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "settings.drf.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Blog API",
    "DESCRIPTION": "Homework 2 Blog API",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False, 
}

LOCALE_PATHS = [BASE_DIR / "locale"]

AUTH_USER_MODEL = "users.User"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        }
    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
        },
        "debug_requests_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "debug_requests.log"),
            "formatter": "verbose",
            "filters": ["require_debug_true"],
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
        },
    },
    "loggers": {
        "users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "blog": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "debug_requests": {
            "handlers": ["debug_requests_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
    ("kk", "Kazakh"),
]

USE_I18N = True
TIME_ZONE = "UTC"
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@blog.com"

ASGI_APPLICATION = 'settings.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

CELERY_BROKER_URL = CELERY_BROKER_URL
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ("json",)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE_FILENAME = os.environ.get(
    "CELERY_BEAT_SCHEDULE_FILENAME",
    str(BASE_DIR / "celerybeat-schedule"),
)
