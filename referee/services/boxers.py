from datetime import date

from referee.models import Boxer, BoxerRoom


def dell_trainer_boxers_to_room(room, trainer):
    BoxerRoom.objects.filter(room=room, trainer=trainer).delete()


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
