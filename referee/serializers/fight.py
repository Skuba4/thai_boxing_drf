from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from referee.models import Boxer, BoxerRoom, Fight, FightSlot


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

    class Meta:
        model = FightSlot
        read_only_fields = ("resolved_boxer",)
        fields = ("corner", "boxer", "source_fight", "resolved_boxer")


class FightSerializer(serializers.ModelSerializer):
    """БОЙ"""

    slots = FightSlotSerializer(many=True, required=False)

    class Meta:
        model = Fight
        fields = ("ring", "number", "stage", "slots", "winner")

    def validate(self, data):
        slots_data = data.get("slots")

        if self.instance is None:
            if not slots_data:
                raise ValidationError("Нужно передать 2 slots для создания боя")
        elif slots_data is None:
            return data

        if len(slots_data) != 2:
            raise ValidationError("У боя должно быть ровно 2 slots")

        corners = {slot.get("corner") for slot in slots_data}
        if corners != {FightSlot.Corner.BLUE, FightSlot.Corner.RED}:
            raise ValidationError("Должны быть slots с corner=blue и corner=red")

        for slot in slots_data:
            boxer = slot.get("boxer")
            source_fight = slot.get("source_fight")

            if boxer is None and source_fight is None:
                raise ValidationError("Заполни boxer или source_fight")

            if boxer is not None and source_fight is not None:
                raise ValidationError("Нельзя заполнить и boxer, и source_fight сразу")

        return data

    def create(self, validated_data):
        slots_data = validated_data.pop("slots")
        fight = Fight.objects.create(**validated_data)

        for slot in slots_data:
            FightSlot.objects.create(fight=fight, **slot)

        return fight

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
