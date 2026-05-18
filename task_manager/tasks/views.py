from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Task, Comment

def index(request):
    recent_tasks = Task.objects.select_related('assignee').order_by('-created_at')[:5]
    return render(request, 'tasks/index.html', {'recent_tasks': recent_tasks})

def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Железный способ получить все choices из поля 'status', как бы они ни назывались внутри класса
    status_choices = task._meta.get_field('status').choices
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Превращаем в словарь для быстрой проверки валидности ключа
        if new_status in dict(status_choices):
            task.status = new_status
            task.save()
            return redirect('task_detail', task_id=task.id)

    comments = task.comments.select_related('author').order_by('created_at')
    
    context = {
        'task': task,
        'comments': comments,
        'status_choices': status_choices  # Передаем исправленный список в шаблон
    }
    return render(request, 'tasks/task_detail.html', context)

# 2. Добавление комментария
# tasks/views.py
@require_POST
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
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
            'author': request.user,
            text_field_name: comment_text
        }
        
        Comment.objects.create(**comment_kwargs)
        
    return redirect('task_detail', task_id=task.id)