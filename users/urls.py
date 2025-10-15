from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from users.views import RegistrationView

app_name = 'users'

urlpatterns = [
    path('reg/', RegistrationView.as_view(), name='reg'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),      ### логин (access + refresh)
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),           ### обновление access по refresh
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
]


