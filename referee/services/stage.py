from referee.models import Fight, FightSlot, RoomBoxer

STAGE_BY_FIGHT_COUNT = {
    16: "1/16",
    8: "1/8",
    4: "1/4",
    2: "1/2",
    1: "final",
}


def get_stage_by_level_size(level_size):
    """Размерность КАЖДОГО уровня просчета сетки"""
    return STAGE_BY_FIGHT_COUNT.get(level_size // 2, "1/32")


def get_list_objects_and_none(boxers_uuid):
    """Преобразуем [UUID, None, UUID ...] в [obj, None, obj ...]."""
    boxers_uuid_not_none = [boxer_id for boxer_id in boxers_uuid if boxer_id is not None]
    boxers_dict = RoomBoxer.objects.in_bulk(boxers_uuid_not_none, field_name="uuid")

    boxers_obj_and_none = []

    for boxer in boxers_uuid:
        if boxer is None:
            boxers_obj_and_none.append(None)
            continue

        boxers_obj_and_none.append(boxers_dict[boxer])

    return boxers_obj_and_none


def stage(boxers, grid):
    """Построение боев конкретной сетки"""
    grid.fights.all().delete()

    boxers_obj_and_none = get_list_objects_and_none(boxers)
    full_fights = []
    grid_order = 1
    corners = ("red", "blue")

    while len(boxers_obj_and_none) > 1:
        level_size = len(boxers_obj_and_none)
        level_stage = get_stage_by_level_size(level_size)

        fights = []

        for i in range(level_size // 2):
            red = boxers_obj_and_none[i * 2]
            blue = boxers_obj_and_none[i * 2 + 1]
            winner = None

            if isinstance(red, RoomBoxer) and blue is None:
                winner = red
            elif isinstance(blue, RoomBoxer) and red is None:
                winner = blue

            fights.append(
                Fight(
                    grid=grid,
                    grid_order=grid_order + i,
                    stage=level_stage,
                    winner=winner,
                )
            )

        created_fights = Fight.objects.bulk_create(fights)
        full_fights.extend(created_fights)
        grid_order += len(created_fights)

        slots = []

        for i, fight in enumerate(created_fights):
            red = boxers_obj_and_none[i * 2]
            blue = boxers_obj_and_none[i * 2 + 1]

            for corner, obj in zip(corners, (red, blue), strict=True):
                slot_data = {
                    "fight": fight,
                    "corner": corner,
                }

                if isinstance(obj, RoomBoxer):
                    slot_data["boxer"] = obj
                elif isinstance(obj, Fight):
                    slot_data["source_fight"] = obj

                slots.append(FightSlot(**slot_data))

        FightSlot.objects.bulk_create(slots)
        boxers_obj_and_none = created_fights

    return (
        Fight.objects.filter(uuid__in=[fight.uuid for fight in full_fights])
        .select_related("winner")
        .prefetch_related(
            "slots",
            "slots__boxer",
            "slots__source_fight",
            "slots__source_fight__winner",
        )
        .order_by("grid_order")
    )
