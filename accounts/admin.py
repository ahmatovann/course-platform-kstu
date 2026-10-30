# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
# Пользователи в стандартной админке Django (/admin/).
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .emails import make_password, send_account_email
from .models import User


# Ф-1. Форма «Добавить пользователя» для администратора.
# По ТЗ самостоятельной регистрации нет: аккаунт создаёт администратор.
# Админ вводит только почту и имя. Пароль придумывает сайт сам
# и отправляет его человеку на почту вместе с логином.
class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name')
        labels = {'first_name': 'Имя'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Имя обязательно (по умолчанию в Django оно необязательное)
        self.fields['first_name'].required = True


# UserAdmin — готовая страница пользователей Django. Мы показываем почту
# в списке, добавляем поле «Аватар» (Ф-13) и меняем форму создания (Ф-1).
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'is_staff')
    search_fields = ('email', 'first_name')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + (
        ('Профиль (Ф-13)', {'fields': ('avatar',)}),
    )

    # Ф-1. Страница «Добавить пользователя» использует нашу форму:
    # add_form — какая форма, add_fieldsets — какие поля на ней видны.
    add_form = CreateUserForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name'),
            'description': 'Пароль задавать не нужно: сайт придумает его сам '
                           'и отправит человеку на почту вместе с логином.',
        }),
    )

    # save_model вызывается, когда админ нажимает «Сохранить».
    # change=False — пользователя создают впервые, change=True — редактируют.
    def save_model(self, request, obj, form, change):
        if not change:
            # 1. Логин (username) делаем равным почте — вход у нас по почте (Ф-2)
            obj.username = obj.email
            # 2. Сайт сам придумывает пароль; set_password хранит его
            #    в базе только в зашифрованном виде (п. 4.2 ТЗ)
            password = make_password()
            obj.set_password(password)
        # 3. Сохраняем пользователя в базу (готовый код Django)
        super().save_model(request, obj, form, change)
        if not change:
            # 4. Отправляем письмо с логином и паролем (accounts/emails.py)
            if send_account_email(request, obj, password):
                self.message_user(
                    request,
                    f'Аккаунт создан. Логин и пароль отправлены на {obj.email}.',
                    messages.SUCCESS,
                )
            else:
                # Если почта не сработала (нет интернета, неверный пароль Gmail),
                # админ видит пароль сам и может передать его человеку.
                self.message_user(
                    request,
                    f'Аккаунт создан, но письмо не отправилось. '
                    f'Передайте человеку: логин {obj.email}, пароль {password}',
                    messages.WARNING,
                )
