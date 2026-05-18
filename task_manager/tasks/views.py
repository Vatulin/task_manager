from django.shortcuts import render
from .models import Task

def index(request):
    recent_tasks = Task.objects.select_related('assignee').order_by('-created_at')[:5]
    
    context = {
        'recent_tasks': recent_tasks,
    }
    return render(request, 'tasks/index.html', context)