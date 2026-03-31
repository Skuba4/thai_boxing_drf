from datetime import date

from rest_framework.exceptions import ValidationError

from referee.models import Boxer, BoxerRoom, Fight, FightSlot


def dell_trainer_boxers_to_room(room, trainer):
    boxers = BoxerRoom.objects.filter(room=room, trainer=trainer)
    fight_ids = list(
        FightSlot.objects.filter(boxer__in=boxers).values_list("fight_id", flat=True)
    )
    Fight.objects.filter(id__in=fight_ids).delete()

    boxers.delete()


def add_trainer_boxers_to_room(room, trainer):
    dell_trainer_boxers_to_room(room, trainer)

    boxers = Boxer.objects.filter(trainer=trainer)
    today = date.today()

    room_boxers = []

    for boxer in boxers:
        age = (
            today.year
            - boxer.birth_date.year
            - (
                (today.month, today.day)
                < (boxer.birth_date.month, boxer.birth_date.day)
            )
        )

        weight_category = "Заглушка"

        room_boxers.append(
            BoxerRoom(
                first_name=boxer.first_name,
                last_name=boxer.last_name,
                middle_name=boxer.middle_name,
                birth_date=boxer.birth_date,
                age=age,
                sex=boxer.sex,
                rank=boxer.rank,
                weight=boxer.weight,
                weight_category=weight_category,
                trainer=trainer,
                room=room,
                source_boxer=boxer,
            )
        )

    BoxerRoom.objects.bulk_create(room_boxers)


def validate_min_boxer_age(value):
    today = date.today()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age < 5:
        raise ValidationError("Минимальный возраст 5 лет")
    return value


def update_availability(boxers, value):
    for boxer in boxers:
        boxer.is_available = value

    BoxerRoom.objects.bulk_update(boxers, ["is_available"])
