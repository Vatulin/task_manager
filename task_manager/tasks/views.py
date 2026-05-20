from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Task, Comment
from .forms import TaskForm

@login_required
def index(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Базовый запрос ко всем задачам системы с оптимизацией связей
    queryset = Task.objects.select_related('assignee__profile').order_by('-created_at')
    
    # 1. АДМИНИСТРАТОР: видит вообще всё
    if profile and profile.role == 'admin':
        recent_tasks = queryset[:5]
        
    # 2. РУКОВОДИТЕЛЬ КОМАНДЫ (team_lead): видит только задачи СВОЕГО отдела
    elif profile and profile.role == 'team_lead':
        # Находим только те задачи, у которых исполнитель (assignee) 
        # принадлежит к тому же отделу (department), что и сам тимлид
        recent_tasks = queryset.filter(assignee__profile__department=profile.department)[:5]
        
    # 3. СОТРУДНИК (employee): видит исключительно СВОИ задачи
    else:
        recent_tasks = queryset.filter(assignee=user)[:5]
        
    return render(request, 'tasks/index.html', {'recent_tasks': recent_tasks})


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # ЖЕСТКАЯ ПРОВЕРКА ПРАВ ДОСТУПА (Защита от перехода по прямой ссылке)
    if profile and profile.role != 'admin':
        
        if profile.role == 'team_lead':
            # Проверяем, есть ли исполнитель у задачи и совпадает ли его отдел с отделом тимлида
            task_assignee_profile = getattr(task.assignee, 'profile', None) if task.assignee else None
            
            if not task_assignee_profile or task_assignee_profile.department != profile.department:
                raise PermissionDenied("Вы можете просматривать задачи только вашего отдела.")
                
        elif profile.role == 'employee':
            # Обычный сотрудник не может зайти в чужую задачу
            if task.assignee != user:
                raise PermissionDenied("У вас нет доступа к этой задаче.")

    # Логика смены статуса (POST)
    status_choices = task._meta.get_field('status').choices
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(status_choices):
            task.status = new_status
            task.save()
            return redirect('tasks:task_detail', task_id=task.id)

    comments = task.comments.select_related('author').order_by('created_at')
    
    context = {
        'task': task,
        'comments': comments,
        'status_choices': status_choices
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Проверка прав на добавление комментариев (по аналогии с детальным просмотром)
    if profile and profile.role != 'admin':
        if profile.role == 'team_lead':
            task_assignee_profile = getattr(task.assignee, 'profile', None) if task.assignee else None
            if not task_assignee_profile or task_assignee_profile.department != profile.department:
                raise PermissionDenied()
        elif profile.role == 'employee':
            if task.assignee != user:
                raise PermissionDenied()

    comment_text = request.POST.get('content', '').strip()
    
    if comment_text:
        all_fields = [f.name for f in Comment._meta.get_fields()]
        if 'text' in all_fields:
            text_field_name = 'text'
        elif 'body' in all_fields:
            text_field_name = 'body'
        else:
            text_field_name = 'content'
            
        comment_kwargs = {
            'task': task,
            'author': user,
            text_field_name: comment_text
        }
        
        Comment.objects.create(**comment_kwargs)
        
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def create_task(request):
    if request.method == 'POST':
            # Передаем request.user, чтобы метод __init__ в форме отработал корректно
            form = TaskForm(request.POST, user=request.user)
            if form.is_valid():
                form.save()
            return redirect('users:dashboard')
    else:
        form = TaskForm(user=request.user)
        
    return render(request, 'tasks/task_form.html', {'form': form})