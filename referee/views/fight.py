from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from referee.models import Boxer, BoxerRoom, Room, Fight
from referee.permissions import IsPremium, IsBoss
from referee.serializers import (
    BoxerSerializer,
    BoxerRoomSerializer,
    FightSerializer,
    EmptySerializer,
)
from referee.services.boxers_room import add_trainer_boxers_to_room


@extend_schema(tags=["Боксеры USER"])
@extend_schema_view(
    list=extend_schema(summary="Список"),
    create=extend_schema(summary="Создать"),
    retrieve=extend_schema(summary="Инфа (UUID)"),
    partial_update=extend_schema(summary="Изменить (UUID)"),
    destroy=extend_schema(summary="Удалить (UUID)"),
)
class BoxerViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = Boxer.objects.all()
    serializer_class = BoxerSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "boxer_uuid"

    def get_queryset(self):
        return Boxer.objects.filter(trainer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(trainer=self.request.user)


@extend_schema(tags=["Боксеры ROOM"])
@extend_schema_view(
    list=extend_schema(summary="Список"),
    retrieve=extend_schema(summary="Инфа (UUID)"),
    partial_update=extend_schema(summary="Изменить (UUID)"),
    destroy=extend_schema(summary="Удалить (UUID)"),
)
class BoxerRoomViewSet(ModelViewSet):
    queryset = BoxerRoom.objects.all()
    serializer_class = BoxerRoomSerializer
    http_method_names = ["post", "get", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "boxer_uuid"

    def get_permissions(self):
        if self.action in ["partial_update", "destroy", "sync"]:
            return [IsPremium(), IsBoss()]
        return [IsPremium()]

    def get_queryset(self):
        return BoxerRoom.objects.filter(room__uuid=self.kwargs["room_uuid"])

    def get_serializer_class(self):
        if self.action == "sync":
            return EmptySerializer
        return BoxerRoomSerializer

    @transaction.atomic
    def perform_destroy(self, instance):
        fight_ids = list(instance.fight_slots.values_list("fight_id", flat=True))
        Fight.objects.filter(id__in=fight_ids).delete()
        instance.delete()

    @extend_schema(
        summary="Синхронизировать личный список",
    )
    @action(
        detail=False,
        methods=["post"],
    )
    @transaction.atomic
    def sync(self, request, *args, **kwargs):
        room = Room.objects.get(uuid=self.kwargs["room_uuid"])
        user = request.user

        add_trainer_boxers_to_room(room, user)

        obj = BoxerRoom.objects.filter(room=self.kwargs["room_uuid"], trainer=user)
        serializer = self.get_serializer(obj, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Бои ROOM"])
@extend_schema_view(
    list=extend_schema(summary="Список"),
    create=extend_schema(summary="Создать"),
    retrieve=extend_schema(summary="Инфа (UUID)"),
    partial_update=extend_schema(summary="Изменить (UUID)"),
    destroy=extend_schema(summary="Удалить (UUID)"),
)
class FightViewSet(ModelViewSet):
    queryset = Fight.objects.all()
    serializer_class = FightSerializer
    http_method_names = ["post", "get", "patch", "delete"]

    lookup_field = "id"
    lookup_url_kwarg = "fight_id"

    def get_permissions(self):
        if self.action in ["create", "partial_update", "destroy"]:
            return [IsPremium(), IsBoss()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Fight.objects.filter(room__uuid=self.kwargs["room_uuid"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["room_id"] = self.kwargs["room_uuid"]
        return context

    def perform_create(self, serializer):
        serializer.save(room_id=self.kwargs["room_uuid"])
