from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = "referee"

router = DefaultRouter()
router.register("rooms", RoomViewSet)
router.register("boxers", BoxerViewSet)
router.register("applications", RoomApplicationDecisionViewSet)

urlpatterns = router.urls + [
    path("room/<uuid:room_uuid>/applications/", RoomApplicationView.as_view()),
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
        "room/<uuid:room_uuid>/fights/",
        FightViewSet.as_view(
            {
                "post": "create",
                "get": "list",
            }
        ),
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
]
