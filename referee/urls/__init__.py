from .fight import *
from .referee import *
from .room import *

app_name = "referee"


urlpatterns = [
    *room,
    *referee,
    *fight,
]
