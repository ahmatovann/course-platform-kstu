# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
# Пользователи в стандартной админке Django (/admin/).
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# UserAdmin — готовая страница пользователей Django. Мы только добавляем
# в неё поле «Аватар» и показываем почту в списке.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'is_staff')
    search_fields = ('email', 'first_name')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (
        ('Профиль (Ф-13)', {'fields': ('avatar',)}),
    )
