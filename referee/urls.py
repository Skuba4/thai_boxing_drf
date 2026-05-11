from django.urls import path
from rest_framework.routers import DefaultRouter

from referee.views import (
    RoomViewSet,
    RingViewSet,
    TrainerApplicationAPIView,
    BoxerViewSet,
    RoomBoxerViewSet,
    GridViewSet,
    FightViewSet, JudgeApplicationAPIView, NoteViewSet,
)

app_name = "referee"

router = DefaultRouter()
router.register("rooms", RoomViewSet)
router.register("boxers", BoxerViewSet)


urlpatterns = router.urls + [
    # Ring
    path("room/<uuid:room_uuid>/rings/", RingViewSet.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/ring/<str:ring_name>/", RingViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
    ),


    # TrainerApplication
    path("room/<uuid:room_uuid>/trainer-applications/", TrainerApplicationAPIView.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/trainer-application/", TrainerApplicationAPIView.as_view(
            {
                "get": "get_application",
                "post": "create_application",
                "patch": "create_application",
                "delete": "delete_application",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/trainer-application/<uuid:application_uuid>/", TrainerApplicationAPIView.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),


    # JudgeApplication
    path("room/<uuid:room_uuid>/judge-applications/", JudgeApplicationAPIView.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/judge-application/", JudgeApplicationAPIView.as_view(
            {
                "get": "get_application",
                "post": "create",
                "delete": "delete_application",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/judge-application/<uuid:application_uuid>/", JudgeApplicationAPIView.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/ring/<str:ring_name>/side-judges", JudgeApplicationAPIView.as_view(
            {
                "get": "get_side_judges",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/ring/<str:ring_name>/judge-application/<uuid:application_uuid>/patch-active", JudgeApplicationAPIView.as_view(
            {
                "patch": "patch_active",
            }
        ),
    ),


    # RoomBoxer
    path("room/<uuid:room_uuid>/boxers/", RoomBoxerViewSet.as_view(
            {
                "get": "list",
                "post": "bulk_create",
                "delete": "bulk_destroy",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/boxers/<uuid:boxer_uuid>/", RoomBoxerViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),


    # Grid
    path("room/<uuid:room_uuid>/grids/", GridViewSet.as_view(
            {
                "post": "create",
                "get": "list",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/grid/<uuid:grid_uuid>/", GridViewSet.as_view(
            {
                "post": "stage_create",
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),


    # Fight
    path("room/<uuid:room_uuid>/fights/", FightViewSet.as_view(
            {
                "get": "list",
            }
        )
    ),
    path("room/<uuid:room_uuid>/fight/<uuid:fight_uuid>/", FightViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/fight/<uuid:fight_uuid>/patch-winner/", FightViewSet.as_view(
            {
                "patch": "fight_winner",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/fight/<uuid:fight_uuid>/patch-status/", FightViewSet.as_view(
            {
                "patch": "fight_status",
            }
        ),
    ),
    path("room/<room_uuid>/fights/ring-order/", FightViewSet.as_view(
            {
                "post": "ring_order",
            }
        ),
    ),


    # Note
    path("room/<uuid:room_uuid>/fight/<uuid:fight_uuid>/notes/", NoteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path("room/<uuid:room_uuid>/fight/<uuid:fight_uuid>/my-notes/", NoteViewSet.as_view(
            {
                "get": "get_my_notes",
            }
        ),
    )

]
