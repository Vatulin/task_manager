INSTALLED_APPS = [
    # ... django apps ...
    "users",
    "tasks",
    "ai_assistant",
    "analytics",
]

# Настройки авторизации
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "tasks:task_list"  # или куда ведёт главная страница
LOGOUT_REDIRECT_URL = "users:login"