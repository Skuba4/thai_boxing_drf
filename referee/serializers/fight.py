from django.db import transaction
from rest_framework import serializers

from referee.models import Boxer, RoomBoxer, Fight, FightSlot, GroupBoxer, Group
from referee.services.boxers_room import validate_min_boxer_age
from referee.services.fights import validate_fight_payload
from users.serializers import UserInfoSerializer


class BoxerSerializer(serializers.ModelSerializer):
    """Боксеры тренера"""

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
        return validate_min_boxer_age(value)


class BoxerRoomSerializer(serializers.ModelSerializer):
    """Боксеры конкретной комнаты"""

    trainer = UserInfoSerializer(read_only=True)

    class Meta:
        model = RoomBoxer
        read_only_fields = ("uuid", "trainer", "weight_category")
        fields = (
            "uuid",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "age",
            "sex",
            "rank",
            "weight",
            "weight_category",
            "is_available",
            "trainer",
        )

    def validate_birth_date(self, value):
        return validate_min_boxer_age(value)


class GroupBoxerSerializer(serializers.ModelSerializer):
    boxer = BoxerRoomSerializer(read_only=True)

    boxer_id = serializers.PrimaryKeyRelatedField(
        queryset=RoomBoxer.objects.all(),
        source="boxer",
        write_only=True,
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source="group",
        write_only=True,
    )

    class Meta:
        model = GroupBoxer
        fields = ("id", "boxer", "boxer_id", "group_id")


class GroupBoxerBulkCreateSerializer(serializers.Serializer):
    boxer_ids = serializers.PrimaryKeyRelatedField(
        queryset=RoomBoxer.objects.all(),
        many=True,
        source="boxers",
    )


class GroupBoxerBulkMoveSerializer(serializers.Serializer):
    target_group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source="target_group",
    )
    group_boxer_ids = serializers.PrimaryKeyRelatedField(
        queryset=GroupBoxer.objects.all(),
        many=True,
        source="group_boxers",
    )

    def validate(self, attrs):
        target_group = attrs["target_group"]
        group_boxers = attrs["group_boxers"]

        if not group_boxers:
            raise serializers.ValidationError("Список участников пуст.")

        room_id = target_group.room_id

        for group_boxer in group_boxers:
            if group_boxer.group.room_id != room_id:
                raise serializers.ValidationError(
                    "Нельзя переносить участников между разными комнатами."
                )

        return attrs


class EmptySerializer(serializers.Serializer):
    pass


class FightSlotSerializer(serializers.ModelSerializer):
    """Участники боя"""

    resolved_boxer = serializers.UUIDField(source="resolved_boxer.uuid", read_only=True)

    class Meta:
        model = FightSlot
        fields = ("corner", "boxer", "source_fight", "resolved_boxer")


class FightSerializer(serializers.ModelSerializer):
    """БОЙ"""

    slots = FightSlotSerializer(many=True, required=False)

    class Meta:
        model = Fight
        fields = ("id", "ring", "number", "stage", "slots", "winner")

    def validate(self, data):
        return validate_fight_payload(
            data,
            instance=self.instance,
            context=self.context,
        )

    @transaction.atomic
    def create(self, validated_data):
        slots_data = validated_data.pop("slots")
        fight = Fight.objects.create(**validated_data)

        for slot in slots_data:
            FightSlot.objects.create(fight=fight, **slot)

        return fight

    @transaction.atomic
    def update(self, instance, validated_data):
        slots_data = validated_data.pop("slots", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if slots_data is not None:
            instance.slots.all().delete()
            for slot_data in slots_data:
                FightSlot.objects.create(fight=instance, **slot_data)

        return instance
