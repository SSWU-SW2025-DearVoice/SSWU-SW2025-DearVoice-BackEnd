from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('user_id', 'email', 'nickname', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('user_id', 'email', 'nickname')
    ordering = ('created_at',)

    fieldsets = (
        (None, {'fields': ('user_id', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Personal Info', {'fields': ('nickname',)}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
