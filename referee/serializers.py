from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from referee.models import Room, TrainerApplication, Ring, Boxer, RoomBoxer, FightSlot, Fight, Grid, JudgeApplication, \
    Note
from referee.services.boxer import age_calculation
from users.serializers import BaseInfoSerializer


class RoomSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    my_trainer_application_status = serializers.SerializerMethodField()
    my_judge = serializers.SerializerMethodField()

    class Meta:
        model = Room
        read_only_fields = ("uuid", "is_owner", "my_trainer_application_status", "my_judge")
        fields = (
            "uuid",
            "name",
            "description",
            "start_date",
            "status",
            "is_owner",
            "my_trainer_application_status",
            "my_judge",
        )

    def get_is_owner(self, obj):
        """Хозяин комнаты или нет."""
        return obj.boss_id == self.context.get("request").user.id

    def get_my_trainer_application_status(self, obj):
        """Статус тренерской заявки."""
        applications = getattr(obj, "my_trainer_applications", [])
        application = applications[0] if applications else None

        return application.status if application else None

    def get_my_judge(self, obj):
        """Статус судьи и ринг назначения."""
        applications = getattr(obj, "my_judge_applications", [])
        application = applications[0] if applications else None

        return (
            None if application is None else
            {
                "status": application.status,
                "ring": application.ring,
            }
        )


class RingSerializer(serializers.ModelSerializer):
    my_judge_extended = serializers.SerializerMethodField()

    class Meta:
        model = Ring
        read_only_fields = ("name", "room", "my_judge_extended")
        fields = (
            "name",
            "description",
            "room",
            "status",
            "my_judge_extended",
        )

    def get_my_judge_extended(self, obj):
        request = self.context["request"]
        application = JudgeApplication.objects.filter(
            room=obj.room,
            user=request.user,
            ring=obj.name,
        ).first()

        return (
            None if application is None else
            {
                "role": application.role,
                "is_active": application.is_active,
            }
        )


class BoxerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Boxer
        read_only_fields = ("uuid",)
        fields = (
            "uuid",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "sex",
            "rank",
            "weight",
        )

    def validate_birth_date(self, value):
        """Проверка минимального возраста боксера."""
        if age_calculation(value) < 5:
            raise ValidationError("Минимальный возраст 5 лет")
        return value


class RoomBoxerSerializer(serializers.ModelSerializer):
    trainer = BaseInfoSerializer(read_only=True)

    class Meta:
        model = RoomBoxer
        read_only_fields = ("uuid", "trainer")
        fields = (
            "uuid",
            "first_name",
            "last_name",
            "middle_name",
            "age",
            "sex",
            "rank",
            "weight",
            "is_available",
            "trainer",
        )


class RoomBoxerBulkCreateSerializer(serializers.Serializer):
    boxer_ids = serializers.PrimaryKeyRelatedField(
        queryset=Boxer.objects.all(),
        many=True,
        source="boxers",
    )


class TrainerApplicationSerializers(serializers.ModelSerializer):
    user = BaseInfoSerializer(read_only=True)
    boxers = BoxerSerializer(many=True, read_only=True)

    boxer_ids = serializers.PrimaryKeyRelatedField(
        queryset=Boxer.objects.all(),
        many=True,
        source="boxers",
        write_only=True
    )

    class Meta:
        model = TrainerApplication
        read_only_fields = ("uuid", "user", "room")
        fields = (
            "uuid",
            "user",
            "room",
            "boxer_ids",
            "boxers",
            "status",
        )


class JudgeApplicationSerializers(serializers.ModelSerializer):
    user = BaseInfoSerializer(read_only=True)

    class Meta:
        model = JudgeApplication
        read_only_fields = ("uuid", "user", "room")
        fields = (
            "uuid",
            "status",
            "ring",
            "role",
            "is_active",
            "room",
            "user",
        )


class JudgeApplicationIsActiveSerializers(serializers.Serializer):
    is_active = serializers.BooleanField(write_only=True)


class GridSerializer(serializers.ModelSerializer):
    ring = serializers.SlugRelatedField(
        queryset=Ring.objects.none(),
        slug_field="name",
        allow_null=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        view = self.context.get("view")
        room_uuid = view.kwargs.get("room_uuid") if view else None

        if room_uuid:
            self.fields["ring"].queryset = Ring.objects.filter(room__uuid=room_uuid)

    class Meta:
        model = Grid
        read_only_fields = ("uuid", "room")
        fields = (
            "uuid",
            "name",
            "boxer_list",
            "room",
            "ring",
        )


class StageSerializer(serializers.Serializer):
    boxer_list = serializers.ListField(child=serializers.UUIDField(allow_null=True))


class FightSlotSerializer(serializers.ModelSerializer):
    source_fight = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    resolved_boxer = serializers.SerializerMethodField()

    class Meta:
        model = FightSlot
        fields = ("corner", "boxer", "source_fight", "resolved_boxer")

    def get_resolved_boxer(self, obj):
        """Боксер слота или победитель боя-источника."""
        boxer = obj.resolved_boxer
        return boxer.uuid if boxer else None


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        read_only_fields = ("fight", "judge")
        fields = (
            "red_remark",
            "blue_remark",
            "round",
            "fight",
            "judge",
        )


class FightSerializer(serializers.ModelSerializer):
    slots = FightSlotSerializer(many=True, read_only=True)
    notes = NoteSerializer(many=True, read_only=True)

    class Meta:
        model = Fight
        read_only_fields = ("uuid", "grid", "grid_order", "ring_order", "stage", "slots", "notes")
        fields = (
            "uuid",
            "grid",
            "grid_order",
            "ring_order",
            "stage",
            "slots",
            "winner",
            "notes",
            "status",
        )


class FightWinnerSerializer(serializers.Serializer):
    winner = serializers.UUIDField(write_only=True, required=False, allow_null=True)


class FightStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Fight.Status, default=Fight.Status.INACTIVE)


class FightRingOrderSerializer(serializers.Serializer):
    fights = serializers.JSONField(default=dict)
