from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path("", views.ai_chat, name="ai_chat_page"),
    path("api/chat/", views.ai_chat_api, name="ai_chat_api"),
]