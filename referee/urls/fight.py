from django.urls import path
from rest_framework.routers import DefaultRouter

from referee.views import GroupBoxerViewSet, BoxerViewSet, FightViewSet

router = DefaultRouter()
router.register("boxers", BoxerViewSet)

urlpatterns = router.urls + [
    path(
        "room/<uuid:room_uuid>/fights/",
        FightViewSet.as_view({"post": "create", "get": "list"}),
    ),
    path(
        "room/<uuid:room_uuid>/fight/<int:fight_id>/",
        FightViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "group/<int:group_id>/boxers/",
        GroupBoxerViewSet.as_view(
            {
                "post": "create",
                "get": "list",
            }
        ),
    ),
    path(
        "group/<int:group_id>/boxer/<int:group_boxer_id>/",
        GroupBoxerViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "group/<int:group_id>/boxer/move/",
        GroupBoxerViewSet.as_view(
            {
                "patch": "bulk_move",
            }
        ),
    ),
]
