from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        self.tokens = RefreshToken.for_user(user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data.update({
            "access": str(self.tokens.access_token),
            "refresh": str(self.tokens)
        })
        return response
