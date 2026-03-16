from uuid import UUID

from rest_framework.exceptions import ValidationError

from referee.models import FightSlot


def validate_fight_payload(data, instance=None, context=None):
    slots_data = data.get("slots")
    context = context or {}

    if instance is not None and slots_data is None:
        _validate_winner(data, instance)
        return data

    _validate_slots_required(slots_data, instance)
    _validate_slots_count(slots_data)
    _validate_slots_corners(slots_data)
    _validate_distinct_boxers(slots_data)

    for slot_data in slots_data:
        _validate_single_slot(slot_data, data, instance, context)

    _validate_winner(data, instance, slots_data)
    return data


def _validate_slots_required(slots_data, instance):
    if instance is None and not slots_data:
        raise ValidationError("Нужно передать 2 slots для создания боя")


def _validate_slots_count(slots_data):
    if len(slots_data) != 2:
        raise ValidationError("У боя должно быть ровно 2 slots")


def _validate_slots_corners(slots_data):
    corners = {slot.get("corner") for slot in slots_data}
    expected_corners = {FightSlot.Corner.BLUE, FightSlot.Corner.RED}

    if corners != expected_corners:
        raise ValidationError("Должны быть slots с corner=blue и corner=red")


def _validate_distinct_boxers(slots_data):
    boxers = [slot.get("boxer") for slot in slots_data if slot.get("boxer") is not None]

    if len(boxers) == 2 and boxers[0] == boxers[1]:
        raise ValidationError("Нельзя поставить одного и того же боксера в оба слота")


def _validate_single_slot(slot_data, data, instance, context):
    boxer = slot_data.get("boxer")
    source_fight = slot_data.get("source_fight")

    match (boxer is not None, source_fight is not None):
        case (False, False):
            raise ValidationError("Заполни boxer или source_fight")
        case (True, True):
            raise ValidationError("Нельзя заполнить и boxer, и source_fight сразу")
        case _:
            if source_fight is not None:
                _validate_source_fight(source_fight, data, instance, context)


def _validate_source_fight(source_fight, data, instance, context):
    current_number = data.get("number")
    current_room = _get_current_room(instance, context)
    current_fight_id = getattr(instance, "id", None)

    if current_fight_id is not None and source_fight.id == current_fight_id:
        raise ValidationError("source_fight не может ссылаться на текущий бой")

    if current_room is not None and source_fight.room_id != current_room.id:
        raise ValidationError("source_fight должен быть из той же комнаты")

    if current_number is not None and source_fight.number >= current_number:
        raise ValidationError(
            "source_fight должен ссылаться только на бой с номером меньше текущего"
        )


def _get_current_room(instance, context):
    if instance is not None:
        return instance.room

    room_id = context.get("room_id")
    if room_id is None:
        return None

    return type("RoomRef", (), {"id": UUID(str(room_id))})()


def _validate_winner(data, instance=None, slots_data=None):
    winner = data.get("winner")

    if winner is None:
        return

    resolved_boxer_ids = _get_resolved_boxer_ids(instance, slots_data)

    if winner.id not in resolved_boxer_ids:
        raise ValidationError("winner должен быть одним из участников боя")


def _get_resolved_boxer_ids(instance=None, slots_data=None):
    if slots_data is not None:
        resolved_boxer_ids = set()
        for slot_data in slots_data:
            boxer = slot_data.get("boxer")
            source_fight = slot_data.get("source_fight")

            if boxer is not None:
                resolved_boxer_ids.add(boxer.id)
            elif source_fight is not None and source_fight.winner_id is not None:
                resolved_boxer_ids.add(source_fight.winner_id)
        return resolved_boxer_ids

    if instance is None:
        return set()

    resolved_boxer_ids = set()
    for slot in instance.slots.select_related("boxer", "source_fight__winner"):
        if slot.boxer_id is not None:
            resolved_boxer_ids.add(slot.boxer_id)
        elif slot.source_fight and slot.source_fight.winner_id is not None:
            resolved_boxer_ids.add(slot.source_fight.winner_id)

    return resolved_boxer_ids
