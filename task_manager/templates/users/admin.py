from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Department, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль сотрудника"
    fields = ("department", "role")
    fk_name = "user"

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "first_name", "last_name", "email", "is_staff", "get_role", "get_department")
    list_filter = ("is_staff", "is_superuser", "profile__role", "profile__department")
    search_fields = ("username", "first_name", "last_name", "email", "profile__department__name")

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, "profile") else "-"
    get_role.short_description = "Роль"

    def get_department(self, obj):
        return obj.profile.department.name if hasattr(obj, "profile") and obj.profile.department else "-"
    get_department.short_description = "Отдел"

# Перерегистрация стандартной модели User с нашим инлайном
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Department)