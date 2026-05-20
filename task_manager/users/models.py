from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField("Название отдела", max_length=100, unique=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("employee", "Сотрудник"),
        ("team_lead", "Руководитель команды"),
        ("admin", "Администратор"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        verbose_name="Отдел", 
        null=True, 
        blank=True,
        related_name="profiles"
    )
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default="employee")

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        dept_name = self.department.name if self.department else "Без отдела"
        return f"{self.user.username} | {dept_name} | {self.get_role_display()}"


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        default_department = Department.objects.first()
        
        role = 'admin' if instance.is_superuser else 'employee'
        
        UserProfile.objects.create(
            user=instance, 
            department=default_department,
            role=role
        )
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            default_department = Department.objects.first()
            role = 'admin' if instance.is_superuser else 'employee'
            UserProfile.objects.create(
                user=instance, 
                department=default_department, 
                role=role
            )