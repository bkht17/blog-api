from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"notifications", views.NotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
    path("posts/stream/", views.post_stream_view, name="post-stream"),
]
