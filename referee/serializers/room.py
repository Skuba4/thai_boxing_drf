from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from referee.models import Room, Ring, RoomApplication, Group, GroupBoxer, BoxerRoom
from referee.serializers import GroupBoxerSerializer
from users.serializers import UserInfoSerializer


class RoomSerializer(serializers.ModelSerializer):
    """Комната"""

    is_owner = serializers.SerializerMethodField()
    my_application_status = serializers.SerializerMethodField()
    rings_count = serializers.IntegerField(write_only=True, default=1)

    class Meta:
        model = Room
        read_only_fields = ("uuid",)
        fields = (
            "uuid",
            "name",
            "description",
            "rings_count",
            "start_date",
            "status",
            "is_owner",
            "my_application_status",
        )

    def validate_rings_count(self, value):
        if 1 <= value <= 5:
            return value
        raise ValidationError("Число активных рингов от 1 до 5 включительно")

    @extend_schema_field(bool)
    def get_is_owner(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.boss_id == request.user.id

    def get_my_application_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        application = RoomApplication.objects.filter(
            room=obj,
            user=request.user,
        ).first()

        return application.status if application else None

    def create(self, validated_data):
        validated_data.pop("rings_count", None)
        return super().create(validated_data)


class RingSerializer(serializers.ModelSerializer):
    """Ринг"""

    class Meta:
        model = Ring
        read_only_fields = ("name", "room")
        fields = ("id", "name", "description", "room", "status")


class GroupSerializer(serializers.ModelSerializer):
    ring = RingSerializer(read_only=True)
    boxers = GroupBoxerSerializer(source="groups", many=True, read_only=True)

    ring_id = serializers.PrimaryKeyRelatedField(
        queryset=Ring.objects.all(),
        source="ring",
        write_only=True,
        required=False,
        allow_null=True,
    )
    boxer_ids = serializers.PrimaryKeyRelatedField(
        queryset=BoxerRoom.objects.all(),
        many=True,
        write_only=True,
    )

    class Meta:
        model = Group
        fields = ("id", "room", "name", "ring", "boxers", "ring_id", "boxer_ids")

    @transaction.atomic
    def create(self, validated_data):
        boxers = validated_data.pop("boxer_ids", [])
        group = Group.objects.create(**validated_data)

        GroupBoxer.objects.bulk_create(
            [GroupBoxer(group=group, boxer=boxer) for boxer in boxers]
        )

        return group


class RoomApplicationDecisionSerializers(serializers.ModelSerializer):
    """Заявка на участие в соревнованиях"""

    user = UserInfoSerializer(read_only=True)

    class Meta:
        model = RoomApplication
        read_only_fields = ("uuid", "user", "room")
        fields = (
            "uuid",
            "user",
            "room",
            "status",
        )
