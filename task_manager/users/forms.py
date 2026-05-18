from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=30, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=30, required=True)
    email = forms.EmailField(label="Электронная почта (Email)", required=True)
    
    # Подтягиваем выпадающие списки напрямую из констант вашей модели UserProfile
    department = forms.ChoiceField(label="Отдел организации", choices=UserProfile.DEPARTMENT_CHOICES, required=True)
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