from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Department

class CustomUserAdmin(BaseUserAdmin):
    pass

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'role')
    list_filter = ('department', 'role')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user',)
    
    def has_add_permission(self, request):
        return False