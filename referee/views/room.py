from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.utils import extend_schema, extend_schema_view

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from referee.models import Room, RoomApplication, Ring
from referee.permissions import IsPremium
from referee.serializers import (
    RingSerializers,
    RoomSerializer,
    RoomApplicationDecisionSerializers,
)
from referee.services.boxers import (
    add_trainer_boxers_to_room,
    dell_trainer_boxers_to_room,
)

User = get_user_model()


@extend_schema(
    tags=["Room"],
)
@extend_schema_view(
    list=extend_schema(summary="Список"),
    create=extend_schema(summary="Создать"),
    retrieve=extend_schema(summary="Инфа (UUID)"),
    partial_update=extend_schema(summary="Изменить (UUID)"),
    destroy=extend_schema(summary="Удалить (UUID)"),
)
class RoomViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "room_uuid"

    def get_queryset(self):
        return Room.objects.filter(boss=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        room = serializer.save(boss=user)
        names = ["A", "B", "C", "D", "E"]
        rings = [Ring(room=room, name=names[i]) for i in range(5)]

        Ring.objects.bulk_create(rings)

        with transaction.atomic():
            add_trainer_boxers_to_room(room, user)

    @extend_schema(
        summary="Комнаты всех пользователей",
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def all_room(self, request, *args, **kwargs):
        serializer = self.get_serializer(Room.objects.all(), many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Кнопки"],
    summary="Участие в соревнованиях",
)
class RoomApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        obj, created = RoomApplication.objects.get_or_create(
            room_id=kwargs["room_uuid"], user=request.user
        )

        if created:
            return Response(
                {"message": "Заявка отправлена"}, status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": "Заявка уже есть", "status": obj.status},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Решение по заявкам в ROOM"],
)
@extend_schema_view(
    list=extend_schema(summary="Список"),
    retrieve=extend_schema(summary="Инфа (UUID)"),
    partial_update=extend_schema(summary="Изменить (UUID)"),
    destroy=extend_schema(summary="Удалить (UUID)"),
)
class RoomApplicationDecisionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = RoomApplication.objects.all()
    serializer_class = RoomApplicationDecisionSerializers
    http_method_names = ["get", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "room_uuid"

    def get_queryset(self):
        return RoomApplication.objects.filter(room__boss=self.request.user)

    def perform_update(self, serializer):
        with transaction.atomic():
            application = self.get_object()
            room = application.room

            trainer = application.user
            application = serializer.save()

            match application.status:
                case RoomApplication.Status.YES:
                    add_trainer_boxers_to_room(room, trainer)
                case _:
                    dell_trainer_boxers_to_room(room, trainer)


@extend_schema(
    tags=["Ring"],
)
@extend_schema_view(
    list=extend_schema(summary="Список"),
    retrieve=extend_schema(summary="Инфа"),
    partial_update=extend_schema(summary="Изменить"),
)
class RingViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = Ring.objects.all()
    serializer_class = RingSerializers
    http_method_names = ["get", "patch"]

    lookup_field = "name"
    lookup_url_kwarg = "ring_name"

    def get_queryset(self):
        return Ring.objects.filter(room__uuid=self.kwargs["room_uuid"])
