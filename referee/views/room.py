from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from referee.models import Room, RoomApplication, Ring, Group, BoxerRoom, GroupBoxer
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
    update_availability,
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

    @transaction.atomic
    def perform_destroy(self, instance):
        boxers = [group_boxer.boxer for group_boxer in instance.boxers.all()]
        update_availability(boxers, True)

        instance.delete()


@extend_schema(
    tags=["Работа с заявками комнаты"],
)
class RoomApplicationView(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = RoomApplication.objects.all()
    serializer_class = RoomApplicationDecisionSerializers
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "application_uuid"

    def get_queryset(self):
        return RoomApplication.objects.filter(room__boss=self.request.user)

    @action(
        detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsPremium]
    )
    @transaction.atomic
    def create_application(self, request, *args, **kwargs):
        room = Room.objects.get(uuid=self.kwargs["room_uuid"])

        if room.boss == request.user:
            return Response(
                {"detail": "Хозяин комнаты не может подать заявку."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application, created = RoomApplication.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={"status": RoomApplication.Status.WAIT},
        )

        if not created:
            return Response(
                {"message": "Заявка уже есть", "status": application.status},
                status=status.HTTP_200_OK,
            )

        boxers = serializer.validated_data.get("boxers", [])
        application.boxers.set(boxers)

        return Response(
            {
                "message": "Заявка отправлена",
                "status": application.status,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False, methods=["patch"], permission_classes=[IsAuthenticated, IsPremium]
    )
    @transaction.atomic
    def update_application(self, request, *args, **kwargs):
        room = Room.objects.get(uuid=self.kwargs["room_uuid"])
        application = RoomApplication.objects.get(room=room, user=request.user)

        if application.status != RoomApplication.Status.WAIT:
            return Response(
                {"detail": "Заявка уже обработана."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        boxers = serializer.validated_data.get("boxers", None)
        if boxers is not None:
            application.boxers.set(boxers)

        return Response(
            {"message": "Заявка обновлена.", "status": application.status},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated, IsPremium],
    )
    @transaction.atomic
    def delete_application(self, request, *args, **kwargs):
        room = Room.objects.get(uuid=self.kwargs["room_uuid"])
        application = RoomApplication.objects.get(room=room, user=request.user)

        if application.status != RoomApplication.Status.WAIT:
            return Response(
                {"detail": "Заявка уже обработана."},
                status=status.HTTP_403_FORBIDDEN,
            )

        application.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def perform_update(self, serializer):
        application = self.get_object()
        room = application.room

        trainer = application.user
        application = serializer.save()

        match application.status:
            case RoomApplication.Status.YES:
                add_trainer_boxers_to_room(room, trainer)
            case _:
                dell_trainer_boxers_to_room(room, trainer)

    @transaction.atomic
    def perform_destroy(self, instance):
        room = instance.room
        trainer = instance.user

        dell_trainer_boxers_to_room(room, trainer)
        instance.delete()
