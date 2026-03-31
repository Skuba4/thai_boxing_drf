from django.urls import path
from rest_framework.routers import DefaultRouter

from referee.views import (
    RoomViewSet,
    RoomApplicationView,
    RingViewSet,
    BoxerRoomViewSet,
    GroupViewSet,
)

router = DefaultRouter()
router.register("rooms", RoomViewSet)

urlpatterns = router.urls + [
    path(
        "applications/",
        RoomApplicationView.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/applications/",
        RoomApplicationView.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/application/",
        RoomApplicationView.as_view(
            {
                "post": "create_application",
                "patch": "update_application",
                "delete": "delete_application",
            }
        ),
    ),
    path(
        "room/application/<uuid:application_uuid>/",
        RoomApplicationView.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/rings/",
        RingViewSet.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/ring/<str:ring_name>/",
        RingViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/boxers/",
        BoxerRoomViewSet.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/boxers/<uuid:boxer_uuid>/",
        BoxerRoomViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/boxers/sync/",
        BoxerRoomViewSet.as_view(
            {
                "post": "sync",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/groups/",
        GroupViewSet.as_view(
            {
                "post": "create",
                "get": "list",
            }
        ),
    ),
    path(
        "room/<uuid:room_uuid>/group/<int:group_id>/",
        GroupViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
]
