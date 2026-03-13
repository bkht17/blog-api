from django.utils.translation import gettext_lazy as _

LANGUAGE_EN = 'en'
LANGUAGE_RU = 'ru'
LANGUAGE_KK = 'kk'

SUPPORTED_LANGUAGE_CHOICES = [
    (LANGUAGE_EN, _('English')),
    (LANGUAGE_RU, _('Russian')),
    (LANGUAGE_KK, _('Kazakh')),
]

SUPPORTED_LANGUAGE_CODES = [LANGUAGE_EN, LANGUAGE_RU, LANGUAGE_KK]

DEFAULT_TIMEZONE = 'UTC'