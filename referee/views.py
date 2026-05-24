from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from referee.models import Room, Ring, TrainerApplication, Grid, Fight, Boxer, RoomBoxer, JudgeApplication, Note
from referee.permissions import IsPremium, IsBoss, IsChiefJudge, IsActiveSideJudge, IsChiefJudgeInRing
from referee.serializers import (
    RoomSerializer,
    RingSerializer,
    TrainerApplicationSerializers,
    GridSerializer,
    FightSerializer,
    BoxerSerializer,
    RoomBoxerSerializer,
    RoomBoxerBulkCreateSerializer, StageSerializer, JudgeApplicationSerializers, NoteSerializer,
    FightRingOrderSerializer, FightWinnerSerializer, FightStatusSerializer, JudgeApplicationIsActiveSerializers
)
from referee.services.boxer import (
    add_trainer_boxers_to_room,
    dell_trainer_boxers_to_room,
    delete_boxer_related_fights,
    update_availability
)
from referee.services.stage import stage

User = get_user_model()


@extend_schema_view(
    list=extend_schema(summary="Список СВОИХ соревнований."),
    create=extend_schema(summary="Создать соревнование."),
    partial_update=extend_schema(summary="Изменить параметры СВОЕГО соревнования."),
    destroy=extend_schema(summary="Удалить СВОЕ соревнование."),
)
@extend_schema(tags=["Соревнования."])
class RoomViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsPremium]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "room_uuid"

    def _with_my_applications(self, queryset):
        """Префетчит заявки текущего пользователя для списка комнат."""
        return queryset.prefetch_related(
            Prefetch(
                "trainer_applications",
                queryset=TrainerApplication.objects.filter(user=self.request.user),
                to_attr="my_trainer_applications",
            ),
            Prefetch(
                "judge_applications",
                queryset=JudgeApplication.objects.filter(user=self.request.user),
                to_attr="my_judge_applications",
            )
        )

    def get_queryset(self):
        return self._with_my_applications(Room.objects.filter(boss=self.request.user))

    def perform_create(self, serializer):
        """Создание фиксированного шаблона рингов сразу при создании комнаты."""
        room = serializer.save(boss=self.request.user)
        Ring.objects.bulk_create([Ring(name=i, room=room) for i in ["A", "B", "C", "D", "E"]])

    @extend_schema(summary="ОБЩИЙ список соревнований.")
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def all(self, request, *args, **kwargs):
        """Общедоступный список соревнований."""
        queryset = self._with_my_applications(Room.objects.all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="Список рингов."),
    retrieve=extend_schema(summary="Конкретный ринг."),
    partial_update=extend_schema(summary="Изменение статуса и описания."),
)
@extend_schema(tags=["Ринги."])
class RingViewSet(ModelViewSet):
    queryset = Ring.objects.all()
    serializer_class = RingSerializer
    http_method_names = ["get", "patch"]

    lookup_field = "name"
    lookup_url_kwarg = "ring_name"

    def get_permissions(self):
        return (
            [IsAuthenticated(), IsPremium(), IsBoss()] if self.action == "partial_update" else
            [IsAuthenticated()]
        )

    def get_queryset(self):
        return Ring.objects.filter(room__uuid=self.kwargs["room_uuid"])


@extend_schema(tags=["Тренерские заявки."])
@extend_schema_view(
    list=extend_schema(summary="Список заявок."),
    retrieve=extend_schema(summary="Конкретная заявка."),
    partial_update=extend_schema(summary="Решение по заявке."),
    destroy=extend_schema(summary="Удалить заявку."),
)
class TrainerApplicationAPIView(ModelViewSet):
    queryset = TrainerApplication.objects.all()
    serializer_class = TrainerApplicationSerializers
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "application_uuid"

    def get_permissions(self):
        return (
            [IsAuthenticated(), IsPremium()] if self.action in ["get_application", "create_application",
                                                                "delete_application"] else
            [IsAuthenticated(), IsPremium(), IsBoss()]
        )

    def get_queryset(self):
        return (
            TrainerApplication.objects
            .select_related("user")
            .prefetch_related("boxers")
            .filter(room__boss=self.request.user, room__uuid=self.kwargs["room_uuid"])
        )

    @transaction.atomic
    def perform_update(self, serializer):
        application = serializer.save()
        room = application.room
        trainer = application.user

        match application.status:
            case TrainerApplication.Status.YES:
                add_trainer_boxers_to_room(room, trainer)
            case _:
                dell_trainer_boxers_to_room(room, trainer)

    @transaction.atomic
    def perform_destroy(self, instance):
        room = instance.room
        trainer = instance.user

        dell_trainer_boxers_to_room(room, trainer)
        instance.delete()

    @extend_schema(summary="Получение своей заявки в конкретной комнате.")
    @action(detail=False, methods=["get"])
    def get_application(self, request, *args, **kwargs):
        try:
            application = TrainerApplication.objects.get(room__uuid=self.kwargs["room_uuid"], user=request.user)
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except TrainerApplication.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(summary="Подача / Редактирование заявки на тренерство.")
    @action(detail=False, methods=["post", "patch"])
    @transaction.atomic
    def create_application(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = get_object_or_404(Room, uuid=kwargs["room_uuid"])
        user = request.user

        if room.status != Room.Status.WAIT:
            return Response({"detail": "Прием заявок окончен."}, status=status.HTTP_403_FORBIDDEN)

        if room.boss_id == user.id:
            return Response({"detail": "Нельзя подать заявку самому себе"}, status=status.HTTP_403_FORBIDDEN)

        application, created = TrainerApplication.objects.get_or_create(room=room, user=user)

        if application.status == TrainerApplication.Status.NO:
            return Response({"detail": "Вам отказано в участии."}, status=status.HTTP_403_FORBIDDEN)

        application.boxers.set(serializer.validated_data.get("boxers", []))

        return (
            Response({"detail": "Заявка отправлена."}, status=status.HTTP_201_CREATED) if created else
            Response({"detail": "Заявка обновлена."}, status=status.HTTP_200_OK)
        )

    @extend_schema(summary="Удаление своей заявки.")
    @action(detail=False, methods=["delete"])
    @transaction.atomic
    def delete_application(self, request, *args, **kwargs):
        try:
            application = TrainerApplication.objects.get(room__uuid=kwargs["room_uuid"], user=request.user)

            if application.status == TrainerApplication.Status.WAIT:
                application.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_403_FORBIDDEN)

        except TrainerApplication.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["Судейские заявки (Судьи)."])
@extend_schema_view(
    create=extend_schema(summary="Подать заявку."),
    list=extend_schema(summary="Список заявок."),
    partial_update=extend_schema(summary="Решение по заявке."),
    destroy=extend_schema(summary="Удалить заявку."),
)
class JudgeApplicationAPIView(ModelViewSet):
    queryset = JudgeApplication.objects.all()
    serializer_class = JudgeApplicationSerializers
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "application_uuid"

    def get_permissions(self):
        return (
            [IsAuthenticated()] if self.action in ["get_application", "create", "delete_application"] else
            [IsAuthenticated(), IsChiefJudgeInRing()] if self.action in ["get_side_judges", "patch_active"] else
            [IsAuthenticated(), IsPremium(), IsBoss()]
        )

    def get_queryset(self):
        return (
            JudgeApplication.objects
            .select_related("user")
            .filter(room__boss=self.request.user, room__uuid=self.kwargs["room_uuid"])
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        room = get_object_or_404(Room, uuid=kwargs["room_uuid"])
        user = request.user

        if room.status != Room.Status.WAIT:
            return Response({"detail": "Прием заявок окончен."}, status=status.HTTP_403_FORBIDDEN)

        if getattr(user, "premium", None) and user.premium.is_premium:
            return Response({"detail": "Тренер не может быть судьей."}, status=status.HTTP_403_FORBIDDEN)

        if room.boss_id == user.id:
            return Response({"detail": "Нельзя подать заявку самому себе."}, status=status.HTTP_403_FORBIDDEN)

        application, created = JudgeApplication.objects.get_or_create(room=room, user=user)

        if application.status == JudgeApplication.Status.NO:
            return Response({"detail": "Вам отказано в судействе."}, status=status.HTTP_403_FORBIDDEN)

        return (
            Response({"detail": "Заявка отправлена."}, status=status.HTTP_201_CREATED) if created else
            Response({"detail": "Заявка уже отправлена."}, status=status.HTTP_200_OK)
        )

    @extend_schema(summary="Получение своей заявки в конкретной комнате.")
    @action(detail=False, methods=["get"])
    def get_application(self, request, *args, **kwargs):
        try:
            application = JudgeApplication.objects.get(room__uuid=self.kwargs["room_uuid"], user=request.user)
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        except JudgeApplication.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(summary="Удаление своей заявки.")
    @action(detail=False, methods=["delete"])
    @transaction.atomic
    def delete_application(self, request, *args, **kwargs):
        try:
            application = JudgeApplication.objects.get(room__uuid=kwargs["room_uuid"], user=request.user)

            if application.status == JudgeApplication.Status.WAIT:
                application.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({"detail": "Заявка уже обработана."}, status=status.HTTP_403_FORBIDDEN)

        except JudgeApplication.DoesNotExist:
            return Response({"detail": "Заявка не найдена."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(summary="Получить список боковых судей в ринге.")
    @action(detail=False, methods=["get"])
    def get_side_judges(self, request, *args, **kwargs):
        judges = JudgeApplication.objects.filter(room__uuid=self.kwargs["room_uuid"], ring=self.kwargs["ring_name"],
                                                 role=JudgeApplication.Role.SIDE,
                                                 status=JudgeApplication.Status.YES)
        serializer = self.get_serializer(judges, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Смена статуса активности боковых судей в ринге.")
    @action(detail=True, methods=["patch"], serializer_class=JudgeApplicationIsActiveSerializers)
    @transaction.atomic
    def patch_active(self, request, *args, **kwargs):
        application = get_object_or_404(JudgeApplication, room__uuid=self.kwargs["room_uuid"],
                                        ring=self.kwargs["ring_name"], uuid=self.kwargs["application_uuid"],
                                        role=JudgeApplication.Role.SIDE, status=JudgeApplication.Status.YES)
        serializer = self.get_serializer(instance=application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        application.is_active = serializer.validated_data["is_active"]
        application.save(update_fields=["is_active"])
        return Response({"detail": "Статус изменен."}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary="Список боксеров."),
    retrieve=extend_schema(summary="Конкретный боксер."),
    create=extend_schema(summary="Добавить нового боксера."),
    partial_update=extend_schema(summary="Изменить данные боксера."),
    destroy=extend_schema(summary="Удалить боксера."),
)
@extend_schema(tags=["Боксеры user."])
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
        """Прописываем тренера при сохранении."""
        serializer.save(trainer=self.request.user)


@extend_schema_view(
    list=extend_schema(summary="Список участников соревнования"),
    partial_update=extend_schema(summary="Изменить данные участника"),
    destroy=extend_schema(summary="Удалить участника"),
)
@extend_schema(tags=["Боксеры ROOM (участники соревнования)."])
class RoomBoxerViewSet(ModelViewSet):
    queryset = RoomBoxer.objects.all()
    serializer_class = RoomBoxerSerializer
    http_method_names = ["post", "get", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "boxer_uuid"

    def get_permissions(self):
        return (
            [IsAuthenticated()] if self.action in ["list"] else
            [IsAuthenticated(), IsPremium(), IsBoss()]
        )

    def get_queryset(self):
        return RoomBoxer.objects.select_related("trainer").filter(room__uuid=self.kwargs["room_uuid"])

    @transaction.atomic
    def perform_destroy(self, instance):
        """Ручное удаление всех зависимостей участника и дальнейшее удаление самого участника."""
        # delete_boxer_related_fights(instance) ДОДЕЛАТЬ!
        instance.delete()

    @extend_schema(summary="Добавляем СВОИХ спортсменов в СВОЮ комнату соревнований.",
                   request=RoomBoxerBulkCreateSerializer)
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_create(self, request, *args, **kwargs):
        serializer = RoomBoxerBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = Room.objects.get(uuid=self.kwargs["room_uuid"])
        user = request.user
        boxers = serializer.validated_data["boxers"]
        add_trainer_boxers_to_room(room, user, boxers)

        return Response({"detail": "Участники добавлены."}, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Удалить всех СВОИХ спортсменов из комнаты соревнований")
    @action(detail=False, methods=["delete"])
    @transaction.atomic
    def bulk_destroy(self, request, *args, **kwargs):
        room = Room.objects.get(uuid=self.kwargs["room_uuid"])
        user = request.user
        dell_trainer_boxers_to_room(room, user)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(summary="Список сеток."),
    create=extend_schema(summary="Создать сетку."),
    partial_update=extend_schema(summary="Изменить имя сетки."),
    destroy=extend_schema(summary="Удалить сетку."),
)
@extend_schema(tags=["Сетки."])
class GridViewSet(ModelViewSet):
    queryset = Grid.objects.all()
    serializer_class = GridSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    lookup_field = "uuid"
    lookup_url_kwarg = "grid_uuid"

    def get_permissions(self):
        return (
            [IsAuthenticated()] if self.action in ["list", "retrieve"] else
            [IsAuthenticated(), IsPremium(), IsBoss()]
        )

    def get_queryset(self):
        return Grid.objects.filter(room__uuid=self.kwargs["room_uuid"])

    def get_serializer_class(self):
        return StageSerializer if self.action == "stage_create" else GridSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        grid = serializer.save(room_id=self.kwargs["room_uuid"])
        boxers = list(RoomBoxer.objects.filter(uuid__in=grid.boxer_list))
        update_availability(added=boxers)

    @transaction.atomic
    def perform_update(self, serializer):
        old_set = set(serializer.instance.boxer_list)
        grid = serializer.save(room_id=self.kwargs["room_uuid"])
        new_set = set(grid.boxer_list)

        removed = list(RoomBoxer.objects.filter(uuid__in=(old_set - new_set)))
        added = list(RoomBoxer.objects.filter(uuid__in=(new_set - old_set)))

        update_availability(added=added, removed=removed)

    @transaction.atomic
    def perform_destroy(self, instance):
        boxers = list(RoomBoxer.objects.filter(uuid__in=instance.boxer_list))
        update_availability(removed=boxers)
        instance.delete()

    @extend_schema(summary="Построить сетку.")
    @action(detail=True, methods=["post"], serializer_class=StageSerializer)
    @transaction.atomic
    def stage_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        boxers = serializer.validated_data.get("boxer_list")
        grid = self.get_object()
        stage(boxers, grid)

        return Response({"detail": "Сетка построена."}, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(summary="Список боев."),
    partial_update=extend_schema(summary="Выбрать победителя."),
)
@extend_schema(tags=["Бои."])
class FightViewSet(ModelViewSet):
    queryset = Fight.objects.all()
    serializer_class = FightSerializer
    http_method_names = ["get", "patch", "post"]

    lookup_field = "uuid"
    lookup_url_kwarg = "fight_uuid"

    def get_permissions(self):
        return (
            [IsAuthenticated()] if self.action in ["list", "retrieve"] else
            [IsAuthenticated(), IsChiefJudge()] if self.action in ["fight_winner", "fight_status"] else
            [IsAuthenticated(), IsPremium(), IsBoss()]
        )

    def get_queryset(self):
        return (
            Fight.objects
            .filter(grid__room__uuid=self.kwargs["room_uuid"])
            .select_related("grid", "winner")
            .prefetch_related(
                "slots",
                "slots__boxer",
                "slots__source_fight",
                "slots__source_fight__winner",
                "notes",
                "notes__judge",
            )
            .order_by("grid_id", "grid_order")
        )

    @extend_schema(summary="Выбор победителя боя (главный судья).")
    @action(detail=True, methods=["patch"], serializer_class=FightWinnerSerializer)
    @transaction.atomic
    def fight_winner(self, request, *args, **kwargs):
        fight = self.get_object()
        slots_uuid = [None, ]

        for slot in fight.slots.all():
            if slot.boxer:
                slots_uuid.append(slot.boxer.uuid)
            if slot.source_fight and slot.source_fight.winner:
                slots_uuid.append(slot.source_fight.winner.uuid)

        serializer = self.get_serializer(instance=fight, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        win_boxer = serializer.validated_data.get("winner")

        if win_boxer and win_boxer.uuid not in slots_uuid:
            return Response({"detail": "Боец не найден."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(winner_id=win_boxer)
        return Response({"detail": "Победитель сохранен."}, status=status.HTTP_200_OK)

    @extend_schema(summary="Смена статуса боя для команды боковым судьям.")
    @action(detail=True, methods=["patch"], serializer_class=FightStatusSerializer)
    @transaction.atomic
    def fight_status(self, request, *args, **kwargs):
        fight = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        if new_status == Fight.Status.ACTIVE:
            Fight.objects.filter(
                grid__ring=fight.grid.ring,
                status=Fight.Status.ACTIVE,
            ).exclude(pk=fight.pk).update(status=Fight.Status.INACTIVE)

        fight.status = new_status
        fight.save(update_fields=["status"])

        return Response({"detail": "Статус изменен."}, status=status.HTTP_200_OK)

    @extend_schema(summary="Сохранить порядок боев в ринге.")
    @action(detail=False, methods=["post"], serializer_class=FightRingOrderSerializer)
    @transaction.atomic
    def ring_order(self, request, *args, **kwargs):
        serializer = FightRingOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.get("fights")

        fights = list(
            Fight.objects.filter(
                uuid__in=data.keys(),
                grid__room__uuid=self.kwargs["room_uuid"],
            )
        )

        for fight in fights:
            fight.ring_order = data[str(fight.uuid)]

        Fight.objects.bulk_update(fights, ["ring_order"])

        return Response({"detail": "Порядок сохранен."}, status=status.HTTP_200_OK)


class NoteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    http_method_names = ["get", "post"]

    def get_permissions(self):
        return (
            [IsAuthenticated(), IsActiveSideJudge()] if self.action in ["post", "get_my_notes"] else
            [IsAuthenticated(), IsChiefJudge()]
        )

    def get_queryset(self):
        return Note.objects.filter(fight__grid__room__uuid=self.kwargs["room_uuid"],
                                   fight__uuid=self.kwargs["fight_uuid"])

    def perform_create(self, serializer):
        application = get_object_or_404(JudgeApplication, room__uuid=self.kwargs["room_uuid"], user=self.request.user)
        if application.status != JudgeApplication.Status.YES:
            raise PermissionDenied("Вы не можете создавать записки.")

        serializer.save(judge=application, fight_id=self.kwargs["fight_uuid"])

    @extend_schema(summary="Получить только свои записки.")
    @action(detail=False, methods=["get"])
    def get_my_notes(self, request, *args, **kwargs):
        notes = self.get_queryset().filter(judge__user=request.user)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data)
