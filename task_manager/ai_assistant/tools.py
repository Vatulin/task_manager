# ai_assistant/tools.py
from datetime import date, timedelta
from django.db.models import Count
from tasks.models import Task

def get_db_snapshot() -> str:
    """Возвращает текстовую сводку состояния базы для промпта"""
    total = Task.objects.count()
    overdue = Task.objects.filter(status__in=["new", "in_progress", "review"], deadline__lt=date.today()).count()
    in_progress = Task.objects.filter(status="in_progress").count()
    
    # Находим самые горящие задачи (дедлайн <= завтра)
    urgent = Task.objects.filter(
        status__in=["new", "in_progress", "review"], 
        deadline__lte=date.today() + timedelta(days=1)
    ).values_list('title', flat=True)[:3]
    
    urgent_text = ", ".join(urgent) if urgent else "нет критических"

    return f"""
    ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ:
    - Всего задач: {total}
    - В работе: {in_progress}
    - Просрочено: {overdue}
    - 🔥 Срочные (дедлайн завтра/сегодня): {urgent_text}
    """

def get_task_list(keyword: str = "") -> str:
    """Универсальный поиск. Если keyword пустой - вернет последние 5 задач"""
    qs = Task.objects.all().order_by('-created_at')
    
    if keyword and len(keyword) > 2:
        qs = qs.filter(title__icontains=keyword)
    
    tasks = qs[:5] # Берем только топ-5, чтобы не перегружать ИИ
    if not tasks: return "Задач по запросу не найдено."
    
    result = "СПИСОК ЗАДАЧ:\n"
    for t in tasks:
        result += f"• [{t.get_status_display()}] {t.title} (Дедлайн: {t.deadline})\n"
    return result