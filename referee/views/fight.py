from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from referee.models import Boxer, BoxerRoom, Room, Fight, GroupBoxer
from referee.permissions import IsPremium, IsBoss
from referee.serializers import (
    BoxerSerializer,
    BoxerRoomSerializer,
    FightSerializer,
    EmptySerializer,
    GroupBoxerSerializer,
    GroupBoxerBulkMoveSerializer,
    GroupBoxerBulkCreateSerializer,
)
from referee.services.boxers_room import add_trainer_boxers_to_room


@extend_schema(tags=["Боксеры USER"])
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


@extend_schema(tags=["Боксеры группы"])
class GroupBoxerViewSet(ModelViewSet):
    queryset = GroupBoxer.objects.all()
    serializer_class = GroupBoxerSerializer
    http_method_names = ["post", "get", "patch", "delete"]

    lookup_field = "id"
    lookup_url_kwarg = "group_boxer_id"

    def get_queryset(self):
        return GroupBoxer.objects.filter(group_id=self.kwargs["group_id"])

    def get_permissions(self):
        if self.action in [
            "create",
            "partial_update",
            "destroy",
            "bulk_move",
            "bulk_create",
        ]:
            return [IsPremium(), IsBoss()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_create(self, request, *args, **kwargs):
        serializer = GroupBoxerBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        boxers = serializer.validated_data["boxers"]
        group_id = self.kwargs["group_id"]

        group_boxers = [GroupBoxer(group_id=group_id, boxer=boxer) for boxer in boxers]

        GroupBoxer.objects.bulk_create(group_boxers)

        return Response({"detail": "Участники добавлены."}, status=201)

    @action(detail=False, methods=["patch"])
    @transaction.atomic
    def bulk_move(self, request, *args, **kwargs):
        serializer = GroupBoxerBulkMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_group = serializer.validated_data["target_group"]
        group_boxers = serializer.validated_data["group_boxers"]

        for group_boxer in group_boxers:
            group_boxer.group = target_group

        GroupBoxer.objects.bulk_update(group_boxers, ["group"])

        return Response({"detail": "Участники перенесены."})


@extend_schema(tags=["Бои ROOM"])
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
