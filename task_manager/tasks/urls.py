from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/comment/', views.add_comment, name='add_comment'),
]