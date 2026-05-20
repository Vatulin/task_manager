from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone
from tasks.models import Task
from users.models import UserProfile, Department  # 👈 Импортируем динамическую модель Department
from datetime import timedelta
import json

@login_required
def admin_analytics(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        raise PermissionDenied("Доступ только для администраторов")

    now = timezone.now()

    STATUS_COMPLETED = Task.StatusChoices.COMPLETED.value
    PERIOD_YEAR = Task.PeriodChoices.YEAR.value
    PERIOD_QUARTER = Task.PeriodChoices.QUARTER.value
    PERIOD_MONTH = Task.PeriodChoices.MONTH.value
    PERIOD_WEEK = Task.PeriodChoices.WEEK.value

    departments_stats = []
    db_departments = Department.objects.all()

    for dept in db_departments:
        dept_tasks = Task.objects.filter(department=dept)
        total = dept_tasks.count()
        completed = dept_tasks.filter(status=STATUS_COMPLETED).count()
        overdue = dept_tasks.filter(
            Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)
        ).count()

        departments_stats.append({
            'id': dept.id,               # 👈 ID для генерации корректных URL-адресов
            'name': dept.name,           # Название из БД (например, "ИТ", "HR")
            'users': UserProfile.objects.filter(department=dept).count(), # Кол-во людей в отделе
            'total': total,
            'completed': completed,
            'overdue': overdue,
            'completion_rate': round(completed / total * 100, 1) if total > 0 else 0
        })

    # === 2. Выполнение планов по периодам ===
    periods = {
        'year': {'label': 'Год', 'period_value': PERIOD_YEAR},
        'quarter': {'label': 'Квартал', 'period_value': PERIOD_QUARTER},
        'month': {'label': 'Месяц', 'period_value': PERIOD_MONTH},
        'week': {'label': 'Неделя', 'period_value': PERIOD_WEEK},
    }

    period_stats = {}
    for key, info in periods.items():
        tasks = Task.objects.filter(period=info['period_value'])
        total = tasks.count()
        done = tasks.filter(status=STATUS_COMPLETED).count()
        overdue = tasks.filter(Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)).count()

        period_stats[key] = {
            'label': info['label'],
            'total': total,
            'done': done,
            'overdue': overdue,
            'completion_rate': round(done / total * 100, 1) if total > 0 else 0
        }

    overdue_tasks = Task.objects.filter(
        Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)
    ).select_related('assignee__profile__department', 'parent_task')

    employee_stats = []
    for up in UserProfile.objects.select_related('user', 'department'):
        user_tasks = Task.objects.filter(assignee=up.user)
        total = user_tasks.count()
        if total > 0:
            active = user_tasks.filter(~Q(status=STATUS_COMPLETED)).count()
            completed = user_tasks.filter(status=STATUS_COMPLETED).count()
            overdue_count = user_tasks.filter(
                Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)
            ).count()
            
            employee_stats.append({
                'username': up.user.username,
                'full_name': up.user.get_full_name() or up.user.username,
                'department': up.department.name if up.department else "Не указан",
                'total': total,
                'active': active,
                'completed': completed,
                'overdue': overdue_count
            })
    employee_stats.sort(key=lambda x: x['active'], reverse=True)

    top_employees = employee_stats[:10]
    
    context = {
        'departments_stats': departments_stats,
        'period_stats': period_stats,
        'overdue_tasks': overdue_tasks,
        'employee_stats': employee_stats,
        'total_tasks': Task.objects.count(),
        'total_overdue': Task.objects.filter(Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)).count(),
        'employee_labels_json': json.dumps([e['username'] for e in top_employees]),
        'employee_active_json': json.dumps([e['active'] for e in top_employees]),
        'employee_completed_json': json.dumps([e['completed'] for e in top_employees]),
        'employee_overdue_json': json.dumps([e['overdue'] for e in top_employees]),
    }
    return render(request, 'analytics/admin_dashboard.html', context)


@login_required
def department_report(request, department_code=None):
    """
    department_code теперь принимает ID (int) записи из таблицы Department 
    или None для отображения 'Все отделы'
    """
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        raise PermissionDenied("Доступ только для администраторов")

    now = timezone.now()
    STATUS_COMPLETED = Task.StatusChoices.COMPLETED.value

    if department_code: 
        current_dept = get_object_or_404(Department, id=department_code)
        tasks = Task.objects.filter(department=current_dept).select_related('assignee__profile')
        department_name = current_dept.name
    else:
        tasks = Task.objects.all().select_related('assignee__profile')
        department_name = 'Все отделы'

    total = tasks.count()
    

    status_counts = {
        'new': tasks.filter(status=Task.StatusChoices.NEW.value).count(),
        'in_progress': tasks.filter(status=Task.StatusChoices.IN_PROGRESS.value).count(),
        'under_review': tasks.filter(status=Task.StatusChoices.UNDER_REVIEW.value).count(),
        'completed': tasks.filter(status=STATUS_COMPLETED).count(),
        'overdue': tasks.filter(Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)).count(),
    }

    period_counts = {
        'year': tasks.filter(period=Task.PeriodChoices.YEAR.value).count(),
        'quarter': tasks.filter(period=Task.PeriodChoices.QUARTER.value).count(),
        'month': tasks.filter(period=Task.PeriodChoices.MONTH.value).count(),
        'week': tasks.filter(period=Task.PeriodChoices.WEEK.value).count(),
    }

    context = {
        'tasks': tasks,
        'department_name': department_name,
        'department_code': department_code,
        'status_counts': status_counts,
        'period_counts': period_counts,
        'total': total,
        'now': now,
    }
    return render(request, 'analytics/department_report.html', context)