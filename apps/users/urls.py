from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoggingTokenObtainPairView, UserPreferenceViewSet

router = DefaultRouter()
router.register(r"register", RegisterViewSet, basename="register")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", LoggingTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "language/",
        UserPreferenceViewSet.as_view({"patch": "language"}),
        name="user-language-update",
    ),
    path(
        "timezone/",
        UserPreferenceViewSet.as_view({"patch": "timezone"}),
        name="user-timezone-update",
    ),
]
