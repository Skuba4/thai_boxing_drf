from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import RegistrationView, PremiumApplicationView, UserInfoViewSet

app_name = "users"

urlpatterns = [
    path("register/", RegistrationView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", TokenBlacklistView.as_view()),
    path("premium/", PremiumApplicationView.as_view()),
    path(
        "profile/",
        UserInfoViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
    ),
]
