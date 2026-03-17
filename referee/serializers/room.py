from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from referee.models import Room, Ring, RoomApplication


class RoomSerializer(serializers.ModelSerializer):
    """Комната"""

    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Room
        read_only_fields = ("uuid",)
        fields = ("uuid", "name", "description", "start_date", "status", "is_owner")

    @extend_schema_field(bool)
    def get_is_owner(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.boss_id == request.user.id


class RingSerializers(serializers.ModelSerializer):
    """Ринг"""

    class Meta:
        model = Ring
        read_only_fields = ("name", "room")
        fields = ("id", "name", "room", "status", "description")


class RoomApplicationDecisionSerializers(serializers.ModelSerializer):
    """Заявка на участие в соревнованиях"""

    class Meta:
        model = RoomApplication
        read_only_fields = ("uuid",)
        fields = ("uuid", "status")
