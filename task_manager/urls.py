from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import path, include
from ai_assistant.views import (
    get_ai_analytics_api,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path("api/ai-report/", get_ai_analytics_api, name="ai_report_api"),
]