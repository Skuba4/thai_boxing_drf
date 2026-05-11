from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import PremiumApplication
from users.serializers import RegistrationSerializer, ExtendedInfoSerializer, EmptySerializer

User = get_user_model()


class RegistrationView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer


class ProfileAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtendedInfoSerializer
    http_method_names = ["get", "patch"]

    def get_object(self):
        return User.objects.select_related("premium").get(pk=self.request.user.pk)


class PremiumApplicationAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    def create(self, request, *args, **kwargs):
        obj, created = PremiumApplication.objects.get_or_create(user=request.user)

        return (
            Response({"message": "Заявка отправлена, ожидайте."}, status=status.HTTP_201_CREATED) if created else
            Response({"message": "Заявка уже есть."}, status=status.HTTP_200_OK)
        )
