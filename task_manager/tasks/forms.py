from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'profile'):
            user_profile = self.user.profile
            
            # 🔹 Если это team_lead — полностью убираем поле из формы,
            # чтобы Django вообще не пытался его валидировать в POST-запросе
            if user_profile.role == 'team_lead':
                if 'department' in self.fields:
                    del self.fields['department']
            
            # 🔹 Фильтруем исполнителей
            if user_profile.role == 'admin':
                self.fields['assignee'].queryset = self.fields['assignee'].queryset.exclude(
                    id=self.user.id
                )
            else:
                self.fields['assignee'].queryset = self.fields['assignee'].queryset.filter(
                    profile__department=user_profile.department
                ).exclude(id=self.user.id)
            
            # 🔹 Фильтруем родительские задачи
            if 'parent_task' in self.fields:
                if user_profile.role != 'admin':
                    self.fields['parent_task'].queryset = self.fields['parent_task'].queryset.filter(
                        department=user_profile.department
                    )

        # 🎨 Стилизация полей
        input_classes = "w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 transition"
        for field in self.fields.values():
            if field.widget.__class__.__name__ != 'HiddenInput':
                field.widget.attrs.update({'class': input_classes})

    def save(self, commit=True):
        task = super().save(commit=False)
        
        # Подстраховка: если у задачи нет отдела (например, создавал team_lead),
        # автоматически берем отдел из профиля создателя
        if not hasattr(task, 'department') or not task.department:
            if self.user and hasattr(self.user, 'profile'):
                task.department = self.user.profile.department
        
        if commit:
            task.save()
        return task

    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee', 'department', 'deadline', 'priority', 'period', 'parent_task']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }