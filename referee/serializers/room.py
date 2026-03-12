from rest_framework import serializers

from referee.models import Room, Ring, RoomApplication


class RoomSerializer(serializers.ModelSerializer):
    """Комната"""

    class Meta:
        model = Room
        read_only_fields = ("uuid",)
        fields = ("uuid", "name", "description", "start_date", "status")


class RingSerializers(serializers.ModelSerializer):
    """Ринг"""

    class Meta:
        model = Ring
        read_only_fields = ("name", "room")
        fields = ("name", "room", "status", "description")


class RoomApplicationDecisionSerializers(serializers.ModelSerializer):
    """Заявка на участие в соревнованиях"""

    class Meta:
        model = RoomApplication
        read_only_fields = ("uuid",)
        fields = ("uuid", "status")
