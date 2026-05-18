import httpx
import json
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Count, Q
from tasks.models import Task

OLLAMA_URL = getattr(settings, "OLLAMA_URL", "http://localhost:11434/api/chat")
AI_MODEL = getattr(settings, "AI_MODEL", "qwen2.5:7b")

SYSTEM_PROMPT = """Ты AI-ассистент проектного офиса. Анализируй данные из инструментов и давай руководителю краткие управленческие рекомендации. Отвечай ТОЛЬКО на основе полученных данных. Не выдумывай."""

TOOLS = [
    {"type":"function","function":{"name":"get_task_status","description":"Найти задачу по названию и вернуть статус, дедлайн, приоритет, ответственного.","parameters":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"]}}},
    {"type":"function","function":{"name":"get_overdue_risks","description":"Найти просроченные задачи и задачи в риске (дедлайн ≤ сегодня+2 дня).","parameters":{"type":"object","properties":{"department":{"type":"string"}}}}},
    {"type":"function","function":{"name":"get_workload","description":"Показать загрузку сотрудников по активным задачам (в работе, на согласовании).","parameters":{"type":"object","properties":{"employee":{"type":"string"}}}}}
]

def _call_ollama(messages, tools=None):
    payload = {"model": AI_MODEL, "messages": messages, "stream": False, "temperature": 0.2}
    if tools: payload["tools"] = tools
    resp = httpx.post(OLLAMA_URL, json=payload, timeout=20.0)
    resp.raise_for_status()
    return resp.json()

def _execute_tool(name, args):
    try:
        if name == "get_task_status":
            t = Task.objects.filter(title__icontains=args.get("title","")).first()
            return {"found": False, "msg": "Не найдена"} if not t else {
                "title": t.title, "status": t.get_status_display(), "deadline": str(t.deadline),
                "assignee": (t.assignee.get_full_name() or t.assignee.username) if t.assignee else "Н/А"
            }
        elif name == "get_overdue_risks":
            qs = Task.objects.filter(status__in=["new","in_progress","review"], deadline__lte=date.today()+timedelta(days=2))
            if args.get("department"): qs = qs.filter(department__name__icontains=args["department"])
            risks = [{"title": t.title, "assignee": (t.assignee.get_full_name() or t.assignee.username) if t.assignee else "Н/А", "deadline": str(t.deadline)} for t in qs]
            return {"count": len(risks), "tasks": risks}
        elif name == "get_workload":
            qs = Task.objects.filter(status__in=["in_progress","review"])
            if args.get("employee"): qs = qs.filter(Q(assignee__username__icontains=args["employee"]) | Q(assignee__first_name__icontains=args["employee"]))
            data = qs.values("assignee__username").annotate(cnt=Count("id")).order_by("-cnt")
            return {"workload": [{"emp": d["assignee__username"] or "Н/А", "active": d["cnt"]} for d in data]}
        return {"error": "Unknown tool"}
    except Exception as e:
        return {"error": str(e)}

def run_ai_agent(query: str) -> str:
    q = query.lower()
    
    if "статус" in q or "задач" in q:
        # Имитация get_task_status
        title = q.replace("какой статус у задачи", "").replace("?", "").strip()
        t = Task.objects.filter(title__icontains=title).first()
        if not t: return "🔍 Задача не найдена в базе."
        return f" Задача: '{t.title}'\n✅ Статус: {t.get_status_display()}\n📅 Дедлайн: {t.deadline}\n👤 Ответственный: {t.assignee.get_full_name() or t.assignee.username if t.assignee else 'Не назначен'}"
        
    elif "риск" in q or "просроч" in q:
        dept = q.split("отдел")[-1].strip() if "отдел" in q else ""
        risks = Task.objects.filter(status__in=["new","in_progress","review"], deadline__lte=date.today()+timedelta(days=2))
        if dept: risks = risks.filter(department__name__icontains=dept)
        if not risks: return "✅ Задач в риске просрочки не обнаружено."
        lines = [f"⚠️ {t.title} (дедлайн: {t.deadline}, ответственный: {t.assignee.username if t.assignee else 'Н/А'})" for t in risks]
        return f"🚨 Найдено {risks.count()} задач в риске:\n" + "\n".join(lines) + "\n💡 Рекомендация: проведите синхронизацию с ответственными."
        
    elif "загрузк" in q or "перегруз" in q:
        data = Task.objects.filter(status__in=["in_progress","review"]).values("assignee__username").annotate(cnt=Count("id")).order_by("-cnt")[:3]
        if not data: return "ℹ️ Активных задач нет."
        lines = [f"👤 {d['assignee__username'] or 'Не назначен'}: {d['cnt']} актив. задач" for d in data]
        return "📈 Топ загруженных сотрудников:\n" + "\n".join(lines)
        
    return "🤖 Я могу проверить статус задачи, найти риски просрочки или показать загрузку сотрудников. Спросите, например: 'Какие задачи в риске?'"