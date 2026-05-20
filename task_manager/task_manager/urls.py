from django.contrib import admin
from django.urls import path, include
from users.views import profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls', namespace='tasks')),
    path('users/', include('users.urls', namespace='users')),
    path('accounts/profile/', profile_view, name='user_profile'),
    path('ai/', include('ai_assistant.urls')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
]

