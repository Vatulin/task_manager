from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout

@login_required
def dashboard(request):
    """Главная страница после входа (позже сюда можно вынести список задач сотрудника)"""
    return render(request, "users/dashboard.html", {
        "user": request.user,
        "role": request.user.profile.get_role_display(),
        "department": request.user.profile.department
    })

def custom_logout(request):
    auth_logout(request)
    return redirect("users:login")