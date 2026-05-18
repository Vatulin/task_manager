from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Task, Comment

@login_required
def index(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Базовый QuerySet с оптимизацией запроса к базе
    queryset = Task.objects.select_related('assignee').order_by('-created_at')
    
    # Разграничение прав на просмотр списка задач
    if profile and profile.role == 'admin':
        # Администратор видит абсолютно все задачи
        recent_tasks = queryset[:5]
    elif profile and profile.role == 'team_lead':
        # Руководитель видит задачи сотрудников своего отдела
        recent_tasks = queryset.filter(assignee__profile__department=profile.department)[:5]
    else:
        # Обычный сотрудник видит только те задачи, где он указан исполнителем
        recent_tasks = queryset.filter(assignee=user)[:5]
        
    return render(request, 'tasks/index.html', {'recent_tasks': recent_tasks})


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Проверка прав доступа к конкретной задаче (Security Check)
    if profile and profile.role != 'admin':
        if profile.role == 'team_lead':
            # Тимлид может смотреть только задачи сотрудников своего отдела
            # (Проверяем, совпадает ли отдел исполнителя задачи с отделом тимлида)
            if not task.assignee or getattr(task.assignee, 'profile', None).department != profile.department:
                raise PermissionDenied("У вас нет доступа к задачам чужого отдела.")
        elif profile.role == 'employee':
            # Обычный сотрудник может смотреть только свою задачу
            if task.assignee != user:
                raise PermissionDenied("У вас нет доступа к этой задаче.")

    # Железный способ получить все choices из поля 'status', как бы они ни назывались внутри класса
    status_choices = task._meta.get_field('status').choices
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Превращаем в словарь для быстрой проверки валидности ключа
        if new_status in dict(status_choices):
            task.status = new_status
            task.save()
            return redirect('tasks:task_detail', task_id=task.id)

    comments = task.comments.select_related('author').order_by('created_at')
    
    context = {
        'task': task,
        'comments': comments,
        'status_choices': status_choices  # Передаем исправленный список в шаблон
    }
    return render(request, 'tasks/task_detail.html', context)


# 2. Добавление комментария
@login_required
@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Проверка прав: оставлять комментарии могут только те, у кого есть доступ к задаче
    if profile and profile.role != 'admin':
        if profile.role == 'team_lead':
            if not task.assignee or getattr(task.assignee, 'profile', None).department != profile.department:
                raise PermissionDenied()
        elif profile.role == 'employee':
            if task.assignee != user:
                raise PermissionDenied()

    comment_text = request.POST.get('content', '').strip()
    
    if comment_text:
        # Узнаем, как на самом деле называются текстовые поля в вашей модели Comment
        all_fields = [f.name for f in Comment._meta.get_fields()]
        
        # Определяем правильное имя поля для текста
        if 'text' in all_fields:
            text_field_name = 'text'
        elif 'body' in all_fields:
            text_field_name = 'body'
        else:
            text_field_name = 'content' # резервный вариант
            
        # Формируем аргументы для динамического создания объекта
        comment_kwargs = {
            'task': task,
            'author': user,
            text_field_name: comment_text
        }
        
        Comment.objects.create(**comment_kwargs)
        
    return redirect('tasks:task_detail', task_id=task.id)