from .fight import urlpatterns as fight
from .room import urlpatterns as room

app_name = "referee"


urlpatterns = [
    *room,
    *fight,
]
