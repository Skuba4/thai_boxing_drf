from rest_framework import serializers

from referee.models import Boxer, BoxerRoom, Fight


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


class FightSerializer(serializers.ModelSerializer):
    """Бой"""

    class Meta:
        model = Fight
        read_only_fields = ("uuid",)
        fields = ("uuid", "number", "blue", "red", "winner")
