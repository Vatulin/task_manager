from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.index, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/comment/', views.add_comment, name='add_comment'),
    path('create/', views.create_task, name='create_task'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
]