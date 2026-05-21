from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('admin/', views.admin_analytics, name='admin_analytics'),
    path('admin/department/<str:department_code>/', views.department_report, name='department_report'),
    path('admin/department/', views.department_report, name='all_departments'),
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('kanban/update/', views.update_task_status, name='update_task_status'),
]