from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from users.views import RegistrationView

app_name = 'users'

urlpatterns = [
    path('token/reg/', RegistrationView.as_view(), name='reg'),
    path('token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),      ### логин (access + refresh)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),           ### обновление access по refresh
    path('token/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
]


