from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and getattr(obj, "author_id", None) == request.user.id
        )
