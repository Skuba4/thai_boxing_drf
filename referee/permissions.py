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

    def has_object_permission(self, request, view, obj):
        return obj.room.boss == request.user
