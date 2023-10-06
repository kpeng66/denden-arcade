from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_code>\w+)$', consumers.RoomConsumer.as_asgi()),
    re_path(r'ws/mathgame/(?P<room_code>\w+)$', consumers.MathGameConsumer.as_asgi()),
]
