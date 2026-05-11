from rest_framework.permissions import BasePermission

from referee.models import Room, JudgeApplication


class IsPremium(BasePermission):
    """Проверка премиум-доступа"""

    def has_permission(self, request, view):
        premium = getattr(request.user, "premium", None)
        return bool(premium and premium.is_premium)


class IsBoss(BasePermission):
    """Проверка владения комнатой."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Room):
            return obj.boss == request.user

        if hasattr(obj, "room"):
            return obj.room.boss == request.user

        if hasattr(obj, "grid"):
            return obj.grid.room.boss == request.user

        return False


class IsActiveSideJudge(BasePermission):
    """Проверка, активный боковой судья ринга этого боя или нет."""

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, "grid"):
            return False

        return JudgeApplication.objects.filter(
            room=obj.grid.room,
            user=request.user,
            status=JudgeApplication.Status.YES,
            role=JudgeApplication.Role.SIDE,
            is_active=True,
            ring=obj.grid.ring.name if obj.grid.ring else "",
        ).exists()


class IsChiefJudge(BasePermission):
    """Проверка, судья ринга этого боя или нет."""

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, "grid"):
            return False

        return JudgeApplication.objects.filter(
            room=obj.grid.room,
            user=request.user,
            status=JudgeApplication.Status.YES,
            role=JudgeApplication.Role.BOSS,
            ring=obj.grid.ring.name if obj.grid.ring else "",
        ).exists()


class IsChiefJudgeInRing(BasePermission):
    """Проверка, что пользователь главный судья указанного ринга."""

    def has_permission(self, request, view):
        room_uuid = view.kwargs.get("room_uuid")
        ring_name = view.kwargs.get("ring_name")

        if not room_uuid or not ring_name:
            return False

        return JudgeApplication.objects.filter(
            room__uuid=room_uuid,
            user=request.user,
            status=JudgeApplication.Status.YES,
            role=JudgeApplication.Role.BOSS,
            ring=ring_name,
        ).exists()
