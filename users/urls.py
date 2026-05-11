from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import RegistrationView, PremiumApplicationAPIView, ProfileAPIView

app_name = "users"

urlpatterns = [
    path("register/", RegistrationView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", TokenBlacklistView.as_view()),
    path("premium/", PremiumApplicationAPIView.as_view()),
    path("profile/", ProfileAPIView.as_view()),
]
