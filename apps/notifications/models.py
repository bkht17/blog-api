from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("recipient"),
    )
    comment = models.ForeignKey(
        "blog.Comment",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("comment"),
    )
    is_read = models.BooleanField(default=False, verbose_name=_("is read"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification for {self.recipient} about comment {self.comment.id}"
