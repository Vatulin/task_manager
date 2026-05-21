import requests
from django.conf import settings
from .tools import get_db_snapshot, get_task_list

def route_user_intent(message: str):
    msg = message.lower()
    
    if any(word in msg for word in ["покажи задачи", "список задач", "что в работе"]):
        return "fast_list", get_task_list(keyword="")
    
    if any(word in msg for word in ["статус", "сводка", "отчет", "как дела"]):
        return "fast_snapshot", get_db_snapshot()
    return "llm", None

def talk_to_corporate_ai(user_message, history=None):
    intent, data = route_user_intent(user_message)
    
    if intent == "fast_list":
        return f"Вот последние задачи:\n\n{data}"
    if intent == "fast_snapshot":
        return f"Текущая сводка:\n\n{data}"

    context = get_task_list(keyword=user_message)
    
    if not context or "нет" in context.lower():
        system_context = "В данный момент нет задач, соответствующих запросу."
    else:
        system_context = f"ДАННЫЕ ИЗ БАЗЫ:\n{context}"

    system_content = (
        "Ты — аналитик данных компании 'Транстелематика'.\n"
        "Правила:\n"
        "1. Отвечай кратко и по делу.\n"
        "2. Если данных нет, честно скажи: 'Я не нашел информации по этому запросу'.\n"

        "3. Используй ТОЛЬКО предоставленные данные.\n\n"
        f"{system_context}"
    )

    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 300
        }
    }

    url = getattr(settings, 'OLLAMA_CHAT_URL', 'http://localhost:11434/api/chat')
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        return response.json().get('message', {}).get('content', 'Ошибка генерации.')
    except Exception as e:
        return f"ИИ сейчас недоступен (ошибка: {e})"