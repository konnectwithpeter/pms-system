# support/urls.py

from django.urls import path
from .views import ChatRoomListView, MessageListView

urlpatterns = [
    path('rooms/', ChatRoomListView.as_view(), name='chatroom-list'),
    path('rooms/<str:room_name>/messages/', MessageListView.as_view(), name='message-list'),
]
