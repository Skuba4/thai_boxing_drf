from django.db import transaction

from referee.models import Ring
from referee.services.boxers_room import add_trainer_boxers_to_room


@transaction.atomic
def ring_creates(user, room, count):
    names = ["A", "B", "C", "D", "E"]
    rings = [
        (
            Ring(room=room, name=names[i], status=Ring.Status.YES)
            if i < count
            else Ring(room=room, name=names[i])
        )
        for i in range(5)
    ]

    Ring.objects.bulk_create(rings)
