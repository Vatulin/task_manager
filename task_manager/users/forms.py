from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Department
from tasks.models import Task

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    email = forms.EmailField(label="Электронная почта (Email)", required=True)
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="Отдел организации",
        empty_label="Выберите отдел",
        required=True
    )
    role = forms.ChoiceField(label="Системная роль", choices=UserProfile.ROLE_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # Добавляем стандартные поля профиля к базовым полям авторизации
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        # 1. Сохраняем базового пользователя (в этот момент срабатывает ваш сигнал post_save и создает пустой профиль)
        user = super().save(commit=commit)
        
        if commit:
            # 2. Получаем автоматически созданный профиль и перезаписываем значения из формы
            profile = user.profile
            profile.department = self.cleaned_data['department']
            profile.role = self.cleaned_data['role']
            profile.save()
            
        return user


class InternalUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    email = forms.EmailField(label="Email", required=True)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="Отдел",
        empty_label="Выберите отдел",
        required=True
    )
    role = forms.ChoiceField(label="Роль", choices=UserProfile.ROLE_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, creator_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор роли в зависимости от того, кто создаёт пользователя
        if creator_role == 'admin':
            self.fields['role'].choices = [('team_lead', 'Руководитель команды'), ('employee', 'Сотрудник')]
        else:  # team_lead
            self.fields['role'].choices = [('employee', 'Сотрудник')]
            self.fields['role'].widget = forms.HiddenInput()  # Скрываем поле, роль фиксирована
            self.fields['role'].initial = 'employee'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            profile.department = self.cleaned_data['department']
            profile.role = self.cleaned_data['role']
            profile.save()
        return user