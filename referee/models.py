import uuid
from datetime import date

from django.db import models
from django.urls import reverse

from users.models import User


class Pupil(models.Model):
    '''СПОРТСМЕНЫ ОТДЕЛЬНОГО ТРЕНЕРА'''
    class Sex(models.TextChoices):
        MALE = 'M', 'Мальчик'
        FEMALE = 'F', 'Девочка'

    class Rank(models.TextChoices):
        A = 'A', 'A'
        B = 'B', 'B'
        C = 'C', 'C'

    first_name = models.CharField(max_length=30, verbose_name='Имя')
    last_name = models.CharField(max_length=30, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=30, verbose_name='Отчество')
    birth_date = models.DateField(verbose_name='Дата рождения')
    sex = models.CharField(max_length=1, choices=Sex.choices, verbose_name='Пол')
    age = models.IntegerField(editable=False, verbose_name='Возраст')
    weight = models.FloatField(verbose_name='Вес')
    weight_category = models.CharField(max_length=20, editable=False, verbose_name='Весовая категория')
    rank = models.CharField(max_length=1, choices=Rank.choices, verbose_name='Класс')
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pupils', verbose_name='Тренер')

    def save(self, *args, **kwargs):
        # возраст выставляется автоматически при сохранении
        if self.birth_date:
            today = date.today()
            self.age = (
                    today.year - self.birth_date.year
                    - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            )

        # весовая и возрастная категория высчитывается автоматически при сохранении
        











        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Room(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активное'
        COMPLETED = 'completed', 'Завершено'

    uuid_room = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=False, verbose_name='Имя комнаты')
    boss = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boss_rooms', verbose_name='Организатор')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, verbose_name='Статус')

    def __str__(self):
        return f'{self.name}'

#
#
# class RoomJudges(models.Model):
#     room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_judges')
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_judges')
#     is_active = models.BooleanField(default=False)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['room', 'user'], name='unique_room_user')
#         ]
#
#     def __str__(self):
#         return 'Промежуточная таблица ROOM-USER'
#
#
# class Fight(models.Model):
#     class Winner(models.TextChoices):
#         FIGHTER_1 = 'fighter_1', 'Боец 1'
#         FIGHTER_2 = 'fighter_2', 'Боец 2'
#
#     uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='fights')
#     number_fight = models.PositiveIntegerField(blank=False)
#     fighter_1 = models.CharField(max_length=50, blank=False)
#     fighter_2 = models.CharField(max_length=50, blank=False)
#     winner = models.CharField(max_length=10, choices=Winner.choices, blank=True, null=True)
#
#     class Meta:
#         ordering = ['room', 'number_fight']
#         constraints = [
#             models.UniqueConstraint(fields=['room', 'number_fight'], name='unique_number_fight_room')
#         ]
#         indexes = [
#             models.Index(fields=['room', 'number_fight']),
#             models.Index(fields=['fighter_1']),
#             models.Index(fields=['fighter_2']),
#         ]
#
#     def __str__(self):
#         return 'Таблица FIGHT'
#
#
# class Notes(models.Model):
#     class Winner(models.TextChoices):
#         RED = "red", "Красный угол"
#         BLUE = "blue", "Синий угол"
#
#     fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name='notes')
#     data = models.DateField(auto_now_add=True)
#     judge = models.CharField(max_length=100)
#     round_number = models.IntegerField()
#     red_fighter = models.CharField(max_length=100)
#     blue_fighter = models.CharField(max_length=100)
#     red_remark = models.CharField(max_length=100)
#     blue_remark = models.CharField(max_length=100)
#     winner = models.CharField(max_length=10, choices=Winner.choices, blank=False)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['fight', 'judge', 'round_number'], name='unique_fight_round')
#         ]
#         indexes = [
#             models.Index(fields=['round_number']),
#         ]
#
#     def __str__(self):
#         return 'Таблица NOTES'
