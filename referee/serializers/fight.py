from django.db import transaction
from rest_framework import serializers

from referee.models import Boxer, BoxerRoom, Fight, FightSlot
from referee.services.fights import validate_fight_payload


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


class BoxerRoomSerializer(serializers.ModelSerializer):
    """Боксеры конкретной комнаты"""

    class Meta:
        model = BoxerRoom
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
            "trainer",
        )


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
        fields = ("ring", "number", "stage", "slots", "winner")

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
