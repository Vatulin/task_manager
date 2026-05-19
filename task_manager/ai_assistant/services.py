import requests
from django.conf import settings
from tasks.models import Task

def get_all_tasks_complete_data():
    tasks = Task.objects.select_related('assignee').all()
    
    if not tasks:
        return "В системе нет задач."
    
    data_lines = []
    for t in tasks:
        assignee = getattr(t.assignee, 'username', 'Не назначен')
        status = t.get_status_display()
        
        line = (
            f"- Задача: '{t.title}' | "
            f"Статус: {status} | "
            f"Ответственный: {assignee} | "
            f"Отдел: {getattr(t, 'department', 'Не указан')} | "
            f"Приоритет: {getattr(t, 'priority', 'Обычный')} | "
            f"Дедлайн: {getattr(t, 'deadline', 'Нет')} | "
            f"Горизонт: {getattr(t, 'planning_horizon', 'Не задан')}"
        )
        data_lines.append(line)
    
    return "\n".join(data_lines)

def talk_to_corporate_ai(user_message, history=None):
    if len(user_message) < 20 and any(w in user_message.lower() for w in ["привет", "как дела", "здравствуй"]):
        all_data = "Пользователь просто здоровается."
    else:
        all_data = get_all_tasks_complete_data()
    system_content = (
        "Ты — аналитик данных компании 'Транстелематика'.\n"
        "Твоя задача — отвечать на вопросы пользователя, основываясь на ПОЛНОМ списке задач.\n"
        "ПРАВИЛА:\n"
        "1. Анализируй весь список задач, предоставленный ниже.\n"
        "2. Не фильтруй данные самостоятельно, если об этом не просит пользователь.\n"
        "3. .\n"
        "3. Будь точен и не выдумывай статус задачи, если его нет в данных.\n\n"
        f"ПОЛНЫЙ СПИСОК ЗАДАЧ:\n{all_data}"
    )

    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2}
    }

    url = getattr(settings, 'OLLAMA_CHAT_URL', 'http://localhost:11434/api/chat')
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        return response.json().get('message', {}).get('content', 'Ошибка ответа.')
    except Exception as e:
        return f"Ошибка связи с ИИ: {e}"