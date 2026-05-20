from django.urls import path
from . import views

urlpatterns = [
    path("", views.ai_chat, name="ai_chat_page"),
    path("api/chat/", views.ai_chat_api, name="ai_chat_api"),
]