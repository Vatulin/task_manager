from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import InternalUserCreationForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from tasks.models import Task 

User = get_user_model()

# 🔒 Декоратор проверки роли
def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            profile = getattr(request.user, 'profile', None)
            user_role = profile.role if profile else None
            if user_role not in allowed_roles:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    role_display = profile.get_role_display() if profile else "Не указана"
    department_display = profile.department.name if profile and profile.department else "Без отдела"
    context = {"user": request.user, "profile": profile, "role": role_display, "department": department_display}
    return render(request, "users/dashboard.html", context)


def custom_logout(request):
    auth_logout(request)
    return redirect("users:login")

@login_required
def profile_view(request, user_id=None):
    if user_id is None:
        user = request.user
        is_own_profile = True
    else:
        user = get_object_or_404(User, id=user_id)
        is_own_profile = (user == request.user)

    profile = getattr(user, 'profile', None)
    tasks = Task.objects.filter(assignee=user)

    # 🔍 Определяем роль текущего залогиненного пользователя
    current_profile = getattr(request.user, 'profile', None)
    current_role = current_profile.role if current_profile else None

    context = {
        'profile_user': user,
        'profile': profile,
        'tasks': tasks,
        'is_own_profile': is_own_profile,
        'can_create_team_lead': current_role == 'admin',
        'can_create_employee': current_role in ['admin', 'team_lead'],
    }
    return render(request, 'users/profile.html', context)


@role_required(['admin'])
def create_team_lead(request):
    if request.method == 'POST':
        form = InternalUserCreationForm(request.POST, creator_role='admin')
        if form.is_valid():
            form.save()
            messages.success(request, "Руководитель команды успешно создан.")
            return redirect('users:dashboard')
    else:
        form = InternalUserCreationForm(creator_role='admin')
    return render(request, 'users/create_team_lead.html', {'form': form, 'title': 'Создание руководителя команды'})


@role_required(['admin', 'team_lead'])
def create_employee(request):
    creator_role = request.user.profile.role
    if request.method == 'POST':
        form = InternalUserCreationForm(request.POST, creator_role=creator_role)
        if form.is_valid():
            form.save()
            messages.success(request, "Сотрудник успешно создан.")
            return redirect('users:dashboard')
    else:
        form = InternalUserCreationForm(creator_role=creator_role)
    return render(request, 'users/create_employee.html', {'form': form, 'title': 'Создание сотрудника'})