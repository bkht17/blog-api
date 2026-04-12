from typing import Any

from celery import shared_task

import logging

logger = logging.getLogger("users")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email(self: Any, user_id: int) -> None:
    from django.contrib.auth import get_user_model

    from apps.users.emails import send_welcome_email as _send_email

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("send_welcome_email: user_id=%s not found, skipping", user_id)
        return

    _send_email(user)
    logger.info("send_welcome_email: sent to user_id=%s email=%s", user_id, user.email)
