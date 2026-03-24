from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import PremiumApplication
from users.serializers import RegistrationSerializer, UserInfoSerializer

User = get_user_model()


@extend_schema(
    summary="Регистрация",
    request=RegistrationSerializer,
)
class RegistrationView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer


@extend_schema_view(
    retrieve=extend_schema(summary="Данные пользователя"),
    partial_update=extend_schema(summary="Обновление"),
)
class UserInfoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer

    http_method_names = [
        "get",
        "patch",
    ]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Кнопки"],
    summary="Премиум доступ",
)
class PremiumApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        obj, created = PremiumApplication.objects.get_or_create(user=request.user)

        if created:
            return Response(
                {"message": "Заявка отправлена"}, status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": "Заявка уже есть", "status": obj.status},
            status=status.HTTP_200_OK,
        )
