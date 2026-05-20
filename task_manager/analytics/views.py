# analytics/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone
from tasks.models import Task
from users.models import UserProfile
from datetime import timedelta
import json

@login_required
def admin_analytics(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        raise PermissionDenied("Доступ только для администраторов")

    now = timezone.now()

    # 🔑 Точные значения из Task.TextChoices
    STATUS_COMPLETED = Task.StatusChoices.COMPLETED.value
    STATUS_OVERDUE = Task.StatusChoices.OVERDUE.value
    PERIOD_YEAR = Task.PeriodChoices.YEAR.value
    PERIOD_QUARTER = Task.PeriodChoices.QUARTER.value
    PERIOD_MONTH = Task.PeriodChoices.MONTH.value
    PERIOD_WEEK = Task.PeriodChoices.WEEK.value

    # === 1. Аналитика по отделам ===
    departments_stats = []
    for dept_code, dept_name in Task.DepartmentChoices.choices:
        dept_tasks = Task.objects.filter(department=dept_code)
        total = dept_tasks.count()
        completed = dept_tasks.filter(status=STATUS_COMPLETED).count()
        overdue = dept_tasks.filter(
            Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)
        ).count()

        departments_stats.append({
            'code': dept_code,
            'name': dept_name,
            'users': UserProfile.objects.filter(department__iexact=dept_code).count(),
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

    # === 3. Просроченные задачи ===
    overdue_tasks = Task.objects.filter(
        Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)
    ).select_related('assignee__profile').order_by('deadline')[:20]

    # === 4. Загрузка сотрудников ===
    employee_stats = []
    for up in UserProfile.objects.select_related('user'):
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
                'department': up.get_department_display(),
                'total': total,
                'active': active,
                'completed': completed,
                'overdue': overdue_count
            })
    employee_stats.sort(key=lambda x: x['active'], reverse=True)

    # Данные для графика (топ-10)
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
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        raise PermissionDenied("Доступ только для администраторов")

    now = timezone.now()
    STATUS_COMPLETED = Task.StatusChoices.COMPLETED.value

    # 🔧 Исправление регистра отдела
    if department_code:
        dept_code_upper = department_code.upper()
        tasks = Task.objects.filter(department__iexact=dept_code_upper).select_related('assignee__profile')
        department_name = dict(Task.DepartmentChoices.choices).get(dept_code_upper, department_code)
    else:
        tasks = Task.objects.all().select_related('assignee__profile')
        department_name = 'Все отделы'

    total = tasks.count()

    # ✅ Подсчёт по статусам (передаём в шаблон)
    status_counts = {
        'new': tasks.filter(status=Task.StatusChoices.NEW.value).count(),
        'in_progress': tasks.filter(status=Task.StatusChoices.IN_PROGRESS.value).count(),
        'under_review': tasks.filter(status=Task.StatusChoices.UNDER_REVIEW.value).count(),
        'completed': tasks.filter(status=STATUS_COMPLETED).count(),
        'overdue': tasks.filter(Q(deadline__lt=now) & ~Q(status=STATUS_COMPLETED)).count(),
    }

    # ✅ Подсчёт по периодам (передаём в шаблон)
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
        'period_counts': period_counts,  # ✅ Добавляем в контекст
        'total': total,
        'now': now,
    }
    return render(request, 'analytics/department_report.html', context)