from rest_framework.permissions import BasePermission

from referee.models import Room
from users.models import PremiumApplication


class IsPremium(BasePermission):
    """Наличие премиум доступа"""

    def has_permission(self, request, view):
        premium_application = getattr(request.user, "premium_application", None)
        return bool(
            premium_application
            and premium_application.status == PremiumApplication.Status.YES
        )


class IsBoss(BasePermission):
    """Создатель комнаты?"""

    def _resolve_room(self, obj):
        if obj is None:
            return None

        if isinstance(obj, Room):
            return obj

        room = getattr(obj, "room", None)
        if room is not None:
            return room

        for relation_name in ("group", "fight", "ring", "boxer"):
            related_obj = getattr(obj, relation_name, None)
            if related_obj is None:
                continue

            related_room = self._resolve_room(related_obj)
            if related_room is not None:
                return related_room

        return None

    def has_object_permission(self, request, view, obj):
        room = self._resolve_room(obj)
        return bool(room and room.boss == request.user)
