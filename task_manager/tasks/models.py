from django.db import models
from django.conf import settings

class Task(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = 'NEW', 'Новая'
        IN_PROGRESS = 'IN_PROGRESS', 'В работе'
        UNDER_REVIEW = 'REVIEW', 'На согласовании'
        COMPLETED = 'COMPLETED', 'Выполнена'
        OVERDUE = 'OVERDUE', 'Просрочена'

    class PeriodChoices(models.TextChoices):
        YEAR = 'YEAR', 'Год'
        QUARTER = 'QUARTER', 'Квартал'
        MONTH = 'MONTH', 'Месяц'
        WEEK = 'WEEK', 'Неделя'

    class PriorityChoices(models.TextChoices):
        LOW = 'LOW', 'Низкий'
        MEDIUM = 'MEDIUM', 'Средний'
        HIGH = 'HIGH', 'Высокий'

    # Перечень отделов из общей оргструктуры компании
    class DepartmentChoices(models.TextChoices):
        HR = 'HR', 'HR'
        AXO = 'AXO', 'АХО'
        IT = 'IT', 'ИТ'
        FINANCE = 'FINANCE', 'Финансы'
        LEGAL = 'LEGAL', 'Юридический отдел'
        TALENTS = 'TALENTS', 'Направление молодых талантов'
        PMO = 'PMO', 'Проектный офис'
    
    def get_status_choices(self):
        return self._meta.get_field('status').choices

    # Основные поля модели по ТЗ
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    
    # Связь с кастомным пользователем из приложения users
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name="Ответственный"
    )
    
    department = models.CharField(
        max_length=50,
        choices=DepartmentChoices.choices,
        verbose_name="Отдел"
    )
    
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    
    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name="Приоритет"
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
        verbose_name="Статус"
    )
    
    period = models.CharField(
        max_length=20,
        choices=PeriodChoices.choices,
        verbose_name="Горизонт планирования"
    )
    
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subtasks',
        verbose_name="Родительская задача",
        help_text="Связь: Годовая цель -> Квартальная задача -> Месячная задача -> Недельная задача"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_period_display()}] {self.title} ({self.get_status_display()})"


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Задача"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']

    def __str__(self):
        return f"Комментарий от {self.author} к задаче №{self.task_id}"