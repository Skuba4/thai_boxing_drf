from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from referee.models import Room, RoomApplication, Ring, Group
from referee.permissions import IsPremium, IsBoss
from referee.serializers import (
    RingSerializer,
    RoomSerializer,
    RoomApplicationDecisionSerializers,
    GroupSerializer,
)
from referee.services.boxers_room import (
    add_trainer_boxers_to_room,
    dell_trainer_boxers_to_room,
)
from referee.services.room import ring_creates

User = get_user_model()


@extend_schema(
    tags=["Комнаты соревнований"],
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
        count = serializer.validated_data.get("rings_count")
        ring_creates(user, room, count)

    @extend_schema(
        summary="Комнаты всех пользователей",
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def all_room(self, request, *args, **kwargs):
        serializer = self.get_serializer(Room.objects.all(), many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Ринги"],
)
class RingViewSet(ModelViewSet):
    queryset = Ring.objects.all()
    serializer_class = RingSerializer
    http_method_names = ["get", "patch"]

    lookup_field = "name"
    lookup_url_kwarg = "ring_name"

    def get_queryset(self):
        return Ring.objects.filter(room__uuid=self.kwargs["room_uuid"])

    def get_permissions(self):
        if self.action in ["create", "partial_update", "destroy"]:
            return [IsPremium(), IsBoss()]
        return [IsAuthenticated()]


@extend_schema(
    tags=["Группы рингов"],
)
class GroupViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "id"
    lookup_url_kwarg = "group_id"

    def get_queryset(self):
        return Group.objects.filter(room__uuid=self.kwargs["room_uuid"])

    def get_permissions(self):
        if self.action in ["create", "partial_update", "destroy"]:
            return [IsPremium(), IsBoss()]
        return [IsAuthenticated()]


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
    tags=["Решения по заявкам в ROOM"],
)
class RoomApplicationDecisionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = RoomApplication.objects.all()
    serializer_class = RoomApplicationDecisionSerializers
    http_method_names = ["get", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "application_uuid"

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

    def perform_destroy(self, instance):
        room = instance.room
        trainer = instance.user

        dell_trainer_boxers_to_room(room, trainer)
        instance.delete()
