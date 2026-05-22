import requests
import json
import re
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from tasks.models import Task

User = get_user_model()


def format_priority(priority_value):
    priority_map = {
        'LOW': 'Низкий',
        'MEDIUM': 'Средний',
        'HIGH': 'Высокий',
        'CRITICAL': 'Критический',
    }
    return priority_map.get(str(priority_value).upper(), 'Не указан')


def format_deadline(deadline):
    if not deadline:
        return 'Не установлен'
    if timezone.is_aware(deadline):
        deadline = timezone.localtime(deadline)
    return deadline.strftime('%d.%m.%Y %H:%M')


def get_all_tasks_complete_data():
    """Сбор всех существующих задач для контекста ИИ-аналитика"""
    tasks = Task.objects.select_related('assignee').all()
    if not tasks:
        return "В системе нет задач."

    data_lines = []
    for t in tasks:
        assignee = getattr(t.assignee, 'username', 'Не назначен')
        status = t.get_status_display() if hasattr(t, 'get_status_display') else getattr(t, 'status', 'Неизвестно')
        priority = format_priority(getattr(t, 'priority', 'NORMAL'))
        deadline = format_deadline(getattr(t, 'deadline', None))
        department = getattr(t, 'department', 'Не указан') or 'Не указан'
        period = t.get_period_display() if hasattr(t, 'get_period_display') else getattr(t, 'period', 'Не указан')

        try:
            task_url = reverse('tasks:task_detail', kwargs={'task_id': t.pk})
        except Exception:
            task_url = f'/task/{t.pk}/'

        task_block = (
            f"• Название: {t.title}\n"
            f"  URL: {task_url}\n"
            f"  Статус: {status}\n"
            f"  Ответственный: {assignee}\n"
            f"  Отдел: {department}\n"
            f"  Приоритет: {priority}\n"
            f"  Дедлайн: {deadline}\n"
            f"  Горизонт: {period}\n"
        )
        data_lines.append(task_block)

    return "\n".join(data_lines)


def get_context_for_task_creation(user):
    """Сбор информации о пользователях и отделах компании для валидации ИИ"""
    context = []
    if hasattr(user, 'profile') and user.profile.department:
        users = User.objects.filter(
            profile__department=user.profile.department
        ).exclude(id=user.id).values_list('username', flat=True)[:10]
        if users:
            context.append(f"Доступные сотрудники отдела: {', '.join(users)}")
    try:
        from users.models import Department
        departments = Department.objects.all().values_list('name', flat=True)[:10]
        if departments:
            context.append(f"Существующие отделы компании: {', '.join(departments)}")
    except Exception:
        pass
    return "; ".join(context) if context else ""


def extract_task_data_from_message(user_message, context_data="", pending_data=None):
    """
    Извлекает параметры задачи из сообщения.
    Если данных не хватает, ИИ возвращает status: 'needs_clarification'
    и формулирует точечный вопрос в missing_info.
    """
    pending_str = json.dumps(pending_data, ensure_ascii=False) if pending_data else "Черновик пуст."
    
    system_prompt = (
        "Ты — строгий корпоративный ИИ-ассистент. Твоя задача — извлечь параметры создаваемой задачи.\n"
        "Ты должен сопоставить новое сообщение пользователя с текущим черновиком задачи и вернуть обновленный объект.\n\n"
        "ПРАВИЛА ИЗВЛЕЧЕНИЯ:\n"
        "1. Заполняй поля в объекте 'data' исключительно на основе реальных фактов из нового сообщения пользователя.\n"
        "2. КРИТИЧЕСКИ ВАЖНО: Если пользователь прямо не указал значение для поля, ставь null и узнавай у пользователя эту информацию преред тем как создать задачу. Никогда не придумывай дефолтные значения (не подставляй MEDIUM, WEEK, it и т.д., если об этом не просили!).\n"
        "3. Если новое сообщение не содержит уточнений для какого-то поля, но это поле уже заполнено в 'ТЕКУЩИЙ ЧЕРНОВИК', обязательно сохрани старое значение из черновика!\n\n"
        "ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ СОЗДАНИЯ ЗАДАЧИ:\n"
        "- title (Название задачи)\n"
        "- description (Подробное описание того, что нужно сделать)\n"
        "- assignee_username (Имя пользователя ответственного сотрудника)\n"
        "- deadline (Срок сдачи в формате YYYY-MM-DD HH:MM)\n\n"
        "ПРАВИЛА ОТВЕТА (ВЫБОР СТАТУСА):\n"
        "- Если хотя бы одно из четырех обязательных полей (title, description, assignee_username, deadline) равно null (отсутствует в черновике и в новом сообщении):\n"
        "  * Установи 'status': 'needs_clarification'\n"
        "  * В поле 'missing_info' напиши один вежливый человеческий вопрос, чтобы узнать ровно ОДНО следующее недостающее поле (например: 'Пожалуйста, укажите описание для задачи' или 'На кого назначить эту задачу?').\n"
        "- Если все 4 обязательных поля успешно собраны, установи 'status': 'ready' и 'missing_info': null.\n\n"
        "Отвечай СТРОГО в формате JSON без разметки markdown, \n"
        "{\n"
        '  "status": "ready" или "needs_clarification",\n'
        '  "missing_info": "Текст вопроса к пользователю или null",\n'
        '  "data": {\n'
        '    "title": "строка или null",\n'
        '    "description": "строка или null",\n'
        '    "assignee_username": "username или null",\n'
        '    "deadline": "YYYY-MM-DD HH:MM или null",\n'
        '    "priority": "LOW|MEDIUM|HIGH|CRITICAL",\n'
        '    "period": "DAY|WEEK|MONTH|QUARTER",\n'
        '    "department": "строка или null"\n'
        "  }\n"
        "}\n"
        "ПРАВИЛА:\n"
        "1. Обязательным полем является 'title'. Если его нет, верни status 'needs_clarification' и спроси пользователя о названии в 'missing_info'.\n"
        "2. Накладывай новые данные поверх старых.\n"
        f"РАНЕЕ СОХРАНЕННЫЕ ДАННЫЕ: {pending_str}\n"
        f"КОНТЕКСТ КОМПАНИИ: {context_data[:400]}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Новое сообщение: {user_message}"}
    ]
    
    payload = {
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    url = getattr(settings, 'OLLAMA_CHAT_URL', 'http://ollama:11434/api/chat')
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json().get('message', {}).get('content', '')
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"Ошибка извлечения данных: {e}")
        return None


def create_task_from_ai(user, task_data):
    if not task_data or not task_data.get('title'):
        return False, "Не указано название задачи."
    
    task_fields = {
        'title': task_data['title'].strip()[:200],
        'description': (task_data.get('description') or '').strip()[:1000],
        'priority': task_data.get('priority', 'MEDIUM').upper(),
        'period': task_data.get('period', 'WEEK').upper(),
    }
    
    if task_fields['priority'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        task_fields['priority'] = 'MEDIUM'
    if task_fields['period'] not in ['DAY', 'WEEK', 'MONTH', 'QUARTER']:
        task_fields['period'] = 'WEEK'
    
    assignee_username = task_data.get('assignee_username')
    if assignee_username:
        try:
            assignee = User.objects.get(username=assignee_username)
            task_fields['assignee'] = assignee
            if not task_data.get('department') and hasattr(assignee, 'profile'):
                task_fields['department'] = assignee.profile.department
        except User.DoesNotExist:
            return False, f"Пользователь '{assignee_username}' не найден."
    
    if task_data.get('department'):
        task_fields['department'] = task_data['department'].strip()[:100]
    
    deadline_str = task_data.get('deadline')
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            task_fields['deadline'] = timezone.make_aware(deadline)
        except ValueError:
            pass
    
    try:
        task = Task.objects.create(**task_fields)
        return True, task
    except Exception as e:
        return False, f"Ошибка БД: {str(e)}"


def talk_to_corporate_ai(user_message, history=None, user=None):
    pending_key = f"pending_task_{user.id}" if user else None
    pending_data = cache.get(pending_key) if pending_key else None

    if pending_data and any(cw in user_message.lower() for cw in ["отмена", "отмени", "стоп"]):
        cache.delete(pending_key)
        return "Создание задачи отменено."

    create_keywords = ["создай задачу", "добавь задачу", "новая задача", "заведи задачу", "создать задачу"]
    
    is_creation_mode = bool(pending_data) or (any(kw in user_message.lower() for kw in create_keywords) and user)

    if is_creation_mode and user:
        context = get_context_for_task_creation(user)
        ai_response = extract_task_data_from_message(user_message, context, pending_data)
        
        if ai_response:
            status = ai_response.get('status', 'ready')
            task_data = ai_response.get('data', {})
            
            if status == 'needs_clarification' or ai_response.get('missing_info'):
                cache.set(pending_key, task_data, timeout=600)
                return f"{ai_response.get('missing_info', 'Уточните параметры задачи.')}"
            
            if pending_key:
                cache.delete(pending_key)
                
            success, result = create_task_from_ai(user, task_data)
            if success:
                task_url = reverse('tasks:task_detail', kwargs={'task_id': result.pk})
                return f"Задача создана: <a href='{task_url}' target='_blank' style='color:#2563eb;font-weight:600;text-decoration:underline'>{result.title}</a><br>Статус: {result.get_status_display()}"
            else:
                return f"Не удалось создать: {result}"
        else:
            return "Не удалось распознать параметры. Напишите 'отмена' для сброса."

    if len(user_message) < 20 and any(w in user_message.lower() for w in ["привет", "как дела", "здравствуй"]):
        all_data = "Пользователь просто здоровается."
    else:
        all_data = get_all_tasks_complete_data()
    
    system_content = (
        "Ты — аналитик данных компании 'Транстелематика'.\n"
        "Отвечай на вопросы, основываясь на списке задач ниже.\n"
        "ПРАВИЛА:\n"
        "1. Не выдумывай статусы и факты.\n"
        "2. КРИТИЧЕСКОЕ ПРАВИЛО: Упоминая задачи, ОБЯЗАТЕЛЬНО оформляй их как кликабельные HTML-ссылки. "
        "Бери URL из данных. Формат: <a href='URL' target='_blank' style='color:#2563eb;font-weight:600;text-decoration:underline'>Название задачи</a>\n\n"
        f"СПИСОК ЗАДАЧ:\n{all_data}"
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

    url = getattr(settings, 'OLLAMA_CHAT_URL', 'http://ollama:11434/api/chat')  
    
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get('message', {}).get('content', 'Ошибка ответа.')
    except Exception as e:
        return f"Ошибка связи с ИИ: {e}"