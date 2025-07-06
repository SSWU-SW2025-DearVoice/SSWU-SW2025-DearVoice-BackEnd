from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('user_id', 'email', 'nickname', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    ordering = ('user_id',)
    search_fields = ('user_id', 'email', 'nickname')

    fieldsets = (
        (None, {'fields': ('user_id', 'email', 'password')}),
        ('개인정보', {'fields': ('nickname',)}),
        ('권한', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_id', 'email', 'nickname', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
