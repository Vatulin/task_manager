from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("employee", "Сотрудник"),
        ("team_lead", "Руководитель команды"),
        ("admin", "Администратор"),
    ]

    DEPARTMENT_CHOICES = [
        ('hr', 'HR'),
        ('aho', 'АХО'),
        ('it', 'ИТ'),
        ('finance', 'Финансы'),
        ('legal', 'Юридический отдел'),
        ('young_talents', 'Направление молодых талантов'),
        ('project_office', 'Проектный офис'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    department = models.CharField("Отдел", max_length=50, choices=DEPARTMENT_CHOICES, default='hr')
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default="employee")

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        return f"{self.user.username} | {self.get_department_display()} | {self.get_role_display()}"


# ОБЪЕДИНЕННЫЙ И БЕЗОПАСНЫЙ СИГНАЛ
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # Если пользователь только что создан, создаем ему профиль
        UserProfile.objects.create(user=instance)
    else:
        # Если пользователь обновляется (например, при входе обновляется last_login),
        # безопасно проверяем существование профиля перед сохранением
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Если профиля почему-то нет (случай с вашим суперюзером egorv), создаем его
            UserProfile.objects.create(user=instance)