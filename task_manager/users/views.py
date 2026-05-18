from django.shortcuts import render, redirect
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm  # Импортируем вашу форму регистрации

@login_required
def dashboard(request):
    """Панель управления сотрудника (Дашборд)"""
    # Безопасно получаем профиль пользователя и текстовые значения роли/отдела
    profile = getattr(request.user, 'profile', None)
    role_display = profile.get_role_display() if profile else "Не указана"
    department_display = profile.get_department_display() if profile else "Не указан"
    
    context = {
        "user": request.user,
        "profile": profile,
        "role": role_display,
        "department": department_display
    }
    return render(request, "users/dashboard.html", context)


def custom_logout(request):
    """Кастомный выход из системы (удобно для хакатона, работает и через GET, и через POST)"""
    auth_logout(request)
    return redirect("users:login")


def register(request):
    """Логика регистрации новых сотрудников и автоматического заполнения профилей"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически авторизуем нового сотрудника после создания
            login(request, user)
            return redirect('users:dashboard')
    else:
        form = UserRegisterForm()
        
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    """Страница личного профиля сотрудника"""
    # Благодаря нашему безопасному сигналу, профиль гарантированно существует
    profile = request.user.profile
    
    context = {
        "user": request.user,
        "profile": profile,
        "role": profile.get_role_display(),
        "department": profile.get_department_display()
    }
    return render(request, "users/profile.html", context)