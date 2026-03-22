import uuid

from django.db import models

from users.models import User


class Boxer(models.Model):
    """
    Боксер из списка тренера

    user.boxers.all() - боксеры конкретного тренера
    """

    class Sex(models.TextChoices):
        BOY = "B", "Мальчик"
        GIRL = "G", "Девочка"

    class Rank(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(blank=True, max_length=30)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex)
    rank = models.CharField(max_length=1, choices=Rank)
    weight = models.DecimalField(max_digits=4, decimal_places=1)

    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boxers")


class BoxerRoom(models.Model):
    """
    Снимок боксера внутри конкретной комнаты

    user.boxers_room.all() - боксеры конкретного тренера
    room.boxers_room.all() - боксеры конкретной комнаты
    source_boxer - поле для обновления отдельных записей
    """

    class Sex(models.TextChoices):
        BOY = "B", "Мальчик"
        GIRL = "G", "Девочка"

    class Rank(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(blank=True, max_length=30)
    birth_date = models.DateField()
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=Sex)
    rank = models.CharField(max_length=1, choices=Rank)
    weight = models.DecimalField(max_digits=4, decimal_places=1)

    weight_category = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)

    trainer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="boxers_room",
    )
    room = models.ForeignKey(
        "referee.Room", on_delete=models.CASCADE, related_name="boxers_room"
    )
    source_boxer = models.ForeignKey(
        Boxer, on_delete=models.SET_NULL, null=True, blank=True
    )


class GroupBoxer(models.Model):
    boxer = models.ForeignKey(
        "referee.BoxerRoom", on_delete=models.CASCADE, related_name="boxers_group"
    )
    group = models.ForeignKey(
        "referee.Group", on_delete=models.CASCADE, related_name="groups"
    )


class Fight(models.Model):
    """
    Бой
    """

    class Stage(models.TextChoices):
        ROUND_OF_32 = "1/32", "1/32"
        ROUND_OF_16 = "1/16", "1/16"
        ROUND_OF_8 = "1/8", "1/8"
        QUARTERFINAL = "1/4", "1/4"
        SEMIFINAL = "1/2", "1/2"
        FINAL = "final", "Финал"

    number = models.PositiveIntegerField()

    ring = models.ForeignKey(
        "referee.Ring",
        on_delete=models.CASCADE,
        related_name="fights",
        null=True,
        blank=True,
    )
    stage = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        choices=Stage,
    )
    winner = models.ForeignKey(
        BoxerRoom,
        on_delete=models.CASCADE,
        related_name="wins",
        null=True,
        blank=True,
    )
    room = models.ForeignKey(
        "referee.Room", on_delete=models.CASCADE, related_name="fights"
    )


class FightSlot(models.Model):
    """
    Участники боя
    """

    class Corner(models.TextChoices):
        BLUE = "blue", "Синий"
        RED = "red", "Красный"

    fight = models.ForeignKey(
        Fight,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    corner = models.CharField(max_length=4, choices=Corner)
    boxer = models.ForeignKey(
        BoxerRoom,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="fight_slots",
    )
    source_fight = models.ForeignKey(
        Fight,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="target_slots",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fight", "corner"], name="uniq_fight_corner"
            ),
        ]

    @property
    def resolved_boxer(self):
        if self.boxer:
            return self.boxer
        if self.source_fight:
            return self.source_fight.winner
        return None
