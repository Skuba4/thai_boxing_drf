from datetime import date

from referee.models import RoomBoxer, Fight, Boxer


def age_calculation(value):
    """Расчет возраста спортсмена по дате."""
    today = date.today()
    age = (today.year - value.year - ((today.month, today.day) < (value.month, value.day)))
    return age


def update_availability(removed=None, added=None):
    """Изменение состояния активности участника (False-прозрачный)."""
    removed = removed or []
    added = added or []

    for boxer in removed:
        boxer.is_available = True
    if removed:
        RoomBoxer.objects.bulk_update(removed, ["is_available"])

    for boxer in added:
        boxer.is_available = False
    if added:
        RoomBoxer.objects.bulk_update(added, ["is_available"])


def delete_boxer_related_fights(instance):
    """Ручное удаление всех зависимостей участника."""
    fight_ids = list(instance.fight_slots.values_list("fight_id", flat=True))
    Fight.objects.filter(id__in=fight_ids).delete()


def dell_trainer_boxers_to_room(room, trainer):
    """Удаление всех спортсменов конкретного тренера, из списка участников."""
    RoomBoxer.objects.filter(room=room, trainer=trainer).delete()


def add_trainer_boxers_to_room(room, trainer, boxers=None):
    """Добавление заявленных спортсменов тренера в список участников."""
    dell_trainer_boxers_to_room(room, trainer)

    if boxers is None:
        boxers = Boxer.objects.filter(trainer_applications__room=room, trainer_applications__user=trainer)

    room_boxers = [RoomBoxer(
        first_name=boxer.first_name,
        last_name=boxer.last_name,
        middle_name=boxer.middle_name,
        age=age_calculation(boxer.birth_date),
        sex=boxer.sex,
        rank=boxer.rank,
        weight=boxer.weight,
        trainer=trainer,
        room=room,
    ) for boxer in boxers]

    RoomBoxer.objects.bulk_create(room_boxers)
