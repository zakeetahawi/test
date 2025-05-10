"""
WebSocket routing configuration for installations app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/installations/(?P<installation_id>\d+)/$',
        consumers.InstallationConsumer.as_asgi()
    ),
]
