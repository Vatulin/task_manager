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
    
    sort_by = request.GET.get('sort', '-created_at')
    
    allowed_sort_fields = {
        '-created_at': '-created_at',
        'created_at': 'created_at',
        'status': 'status',
        'deadline': 'deadline',
        '-priority': '-priority',
    }
    
    order_field = allowed_sort_fields.get(sort_by, '-created_at')
    queryset = Task.objects.select_related('assignee__profile')
    
    if profile and profile.role == 'admin':
        filtered_queryset = queryset
    elif profile and profile.role == 'team_lead':
        filtered_queryset = queryset.filter(assignee__profile__department=profile.department)
    else:
        filtered_queryset = queryset.filter(assignee=user)
        
    recent_tasks = filtered_queryset.order_by(order_field)[:5]
    
    context = {
        'recent_tasks': recent_tasks,
        'current_sort': sort_by
    }
    return render(request, 'tasks/index.html', context)


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    if profile and profile.role != 'admin':
        
        if profile.role == 'team_lead':
            task_assignee_profile = getattr(task.assignee, 'profile', None) if task.assignee else None
            
            if not task_assignee_profile or task_assignee_profile.department != profile.department:
                raise PermissionDenied("Вы можете просматривать задачи только вашего отдела.")
                
        elif profile.role == 'employee':
            if task.assignee != user:
                raise PermissionDenied("У вас нет доступа к этой задаче.")

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
        'status_choices': status_choices,
        'profile': profile,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    user = request.user
    profile = getattr(user, 'profile', None)

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
            form = TaskForm(request.POST, user=request.user)
            if form.is_valid():
                form.save()
            return redirect('users:dashboard')
    else:
        form = TaskForm(user=request.user)
        
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
@require_POST
def task_delete(request, task_id):
    user = request.user
    profile = getattr(user, 'profile', None)
    task = get_object_or_404(Task, id=task_id)
    print(profile.role)
    
    if profile and profile.role == 'admin':
        task.delete()
    elif profile and profile.role == 'team_lead':
        task_department = getattr(task.assignee.profile, 'department', None) if task.assignee else None
        
        if task_department and task_department == profile.department:
            task.delete()
        else:
            raise PermissionDenied("Вы можете удалять задачи только своего отдела.")
    else:
        raise PermissionDenied("У вас недостаточно прав для удаления этой задачи.")
        
    return redirect('tasks:task_list')
