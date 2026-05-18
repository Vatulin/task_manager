from django.contrib import admin
from .models import Task, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'period', 'status', 'priority', 'department', 'assignee', 'deadline')
    list_filter = ('status', 'period', 'priority', 'department')
    search_fields = ('title', 'description')
    inlines = [CommentInline]
    raw_id_fields = ('parent_task', 'assignee')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'author__username')