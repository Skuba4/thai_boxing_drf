import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from referee.constants.grid_names import GRID_NAME_CHOICES

User = get_user_model()


class Room(models.Model):
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
    trainers = models.ManyToManyField(User, related_name="rooms_as_trainer", through="TrainerApplication")


class Ring(models.Model):
    class Status(models.TextChoices):
        YES = "Y", "Используется"
        NO = "N", "Не используется"

    name = models.CharField(max_length=1)
    description = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=1, choices=Status, default=Status.NO)

    room = models.ForeignKey("referee.Room", on_delete=models.CASCADE, related_name="rings")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "name"], name="unique_ring_name_per_room"),
            models.CheckConstraint(condition=Q(name__in=["A", "B", "C", "D", "E"]), name="ring_name_valid"),
        ]


class Boxer(models.Model):
    class Sex(models.TextChoices):
        MALE = "M", "Мальчик"
        FEMALE = "F", "Девочка"

    class Rank(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex)
    rank = models.CharField(max_length=1, choices=Rank)
    weight = models.DecimalField(max_digits=4, decimal_places=1)

    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boxers")


class TrainerApplication(models.Model):
    class Status(models.TextChoices):
        WAIT = "0", "Ожидает"
        YES = "Y", "Одобрено"
        NO = "N", "Отказано"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=Status, default=Status.WAIT)

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="trainer_applications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trainer_applications")
    boxers = models.ManyToManyField(Boxer, related_name="trainer_applications")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_trainer_application_room_user"),
        ]


class JudgeApplication(models.Model):
    class Status(models.TextChoices):
        WAIT = "0", "Ожидает"
        YES = "Y", "Одобрено"
        NO = "N", "Отказано"

    class Role(models.TextChoices):
        BOSS = "chief", "главный"
        SIDE = "side", "боковой"

    class Ring(models.TextChoices):
        NONE = "", "Без ринга"
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=Status, default=Status.WAIT)
    ring = models.CharField(max_length=1, choices=Ring, default=Ring.NONE)
    role = models.CharField(max_length=5, choices=Role, default=Role.SIDE)

    # Статус активности ТОЛЬКО бокового судьи, True активен, False отдыхает.
    is_active = models.BooleanField(default=False)

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="judge_applications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="judge_applications")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_judge_application_room_user"),
        ]


class RoomBoxer(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=1, choices=Boxer.Sex)
    rank = models.CharField(max_length=1, choices=Boxer.Rank)
    weight = models.DecimalField(max_digits=4, decimal_places=1)

    # False участник прозрачный в списке, True готов к взаимодействию.
    is_available = models.BooleanField(default=True)

    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="boxers_room", null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="boxers_room")


class Grid(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40, choices=GRID_NAME_CHOICES)
    boxer_list = models.JSONField(default=list)

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="grids")
    ring = models.ForeignKey(Ring, on_delete=models.CASCADE, related_name="grids", blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "name"], name="uniq_grid_name_per_room"),
        ]


class Fight(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        INACTIVE = "inactive", "Неактивный"

    class Stage(models.TextChoices):
        ROUND_OF_32 = "1/32", "1/32"
        ROUND_OF_16 = "1/16", "1/16"
        ROUND_OF_8 = "1/8", "1/8"
        QUARTERFINAL = "1/4", "1/4"
        SEMIFINAL = "1/2", "1/2"
        FINAL = "final", "Финал"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    ring_order = models.PositiveIntegerField(null=True, blank=True)
    grid_order = models.PositiveIntegerField(null=True, blank=True)
    stage = models.CharField(max_length=5, choices=Stage, null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status, default=Status.INACTIVE)

    grid = models.ForeignKey(Grid, on_delete=models.CASCADE, related_name="fights")
    winner = models.ForeignKey(RoomBoxer, on_delete=models.CASCADE, related_name="wins", null=True, blank=True)


class FightSlot(models.Model):
    class Corner(models.TextChoices):
        RED = "red", "Красный"
        BLUE = "blue", "Синий"

    corner = models.CharField(max_length=4, choices=Corner)

    fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name="slots")
    boxer = models.ForeignKey(RoomBoxer, on_delete=models.CASCADE, related_name="fight_slots", null=True, blank=True)
    source_fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name="target_slots", null=True,
                                     blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["fight", "corner"], name="uniq_fight_corner"),
            models.CheckConstraint(
                condition=~(models.Q(boxer__isnull=False) & models.Q(source_fight__isnull=False)),
                name="fightslot_not_both_boxer_and_source_fight",
            ),
        ]

    @property
    def resolved_boxer(self):
        """Боксер слота или победитель боя-источника."""
        return (
            self.boxer if self.boxer else
            self.source_fight.winner if self.source_fight else
            None
        )


class Note(models.Model):
    class Winner(models.TextChoices):
        NONE = "", "Не выбран"
        RED = "red", "Красный"
        BLUE = "blue", "Синий"

    class Round(models.TextChoices):
        ONE = "1", "Первый"
        TWO = "2", "Второй"
        THREE = "3", "Третий"

    created_at = models.DateTimeField(auto_now_add=True)
    red_remark = models.CharField(max_length=20, blank=True, default="")
    blue_remark = models.CharField(max_length=20, blank=True, default="")
    round = models.CharField(max_length=1, choices=Round, default=Round.ONE)

    fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name='notes')
    judge = models.ForeignKey(JudgeApplication, on_delete=models.CASCADE, related_name='notes')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fight', 'judge', 'round'], name='unique_fight_judge_round')
        ]
