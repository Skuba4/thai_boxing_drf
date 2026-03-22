import uuid
from django.db import models
from django.db.models import Q

from users.models import User


class Room(models.Model):
    """
    Комната соревнований

    room.trainers.all() - все тренера комнаты
    user.rooms_as_trainer.all() - в каких соревнованиях User тренер
    user.boss_rooms.all() - в каких соревнованиях User организатор
    """

    class Status(models.TextChoices):
        WAIT = "0", "Подготовка"
        YES = "Y", "Активно"
        NO = "N", "Завершено"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=50, blank=True)
    start_date = models.DateField()
    status = models.CharField(max_length=1, choices=Status, default=Status.WAIT)

    boss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boss_rooms")
    trainers = models.ManyToManyField(
        User, related_name="rooms_as_trainer", through="RoomApplication"
    )


class Ring(models.Model):
    """
    Ринг

    room.rings.all() - ринги конкретной комнаты
    """

    class Status(models.TextChoices):
        YES = "Y", "Используется"
        NO = "N", "Не используется"

    name = models.CharField(max_length=1)
    description = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=1, choices=Status, default=Status.NO)

    room = models.ForeignKey(
        "referee.Room", on_delete=models.CASCADE, related_name="rings"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["room", "name"], name="unique_ring_name_per_room"
            ),
            models.CheckConstraint(
                condition=Q(name__in=["A", "B", "C", "D", "E"]), name="ring_name_valid"
            ),
        ]


class RoomApplication(models.Model):
    """
    Заявка на участие в соревнованиях

    room.rooms_applications.all() - заявки конкретной КОМНАТЫ
    user.user_applications.all() - заявки конкретного User
    """

    class Status(models.TextChoices):
        WAIT = "0", "Ожидает"
        YES = "Y", "Одобрено"
        NO = "N", "Отказано"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=Status, default=Status.WAIT)

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="rooms_applications"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_applications"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_room_user")
        ]


class Group(models.Model):
    name = models.CharField(max_length=20, blank=False, null=True)
    room = models.ForeignKey(
        "referee.Room", on_delete=models.CASCADE, related_name="rooms_group"
    )
    ring = models.ForeignKey(
        "referee.Ring", on_delete=models.CASCADE, related_name="rings_group"
    )
