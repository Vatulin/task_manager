from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField("Название отдела", max_length=100, unique=True)
    code = models.CharField("Код отдела", max_length=20, blank=True, unique=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("employee", "Сотрудник"),
        ("team_lead", "Руководитель команды"),
        ("admin", "Администратор подразделения"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default="employee")

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        dept = self.department.name if self.department else "Без отдела"
        return f"{self.user.get_full_name() or self.user.username} | {self.get_role_display()} | {dept}"


# Автоматическое создание профиля при регистрации пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()