# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


# Ф-1. Форма регистрации: имя, почта и пароль (два раза)
# UserCreationForm — готовая форма Django: проверяет, что пароли совпадают
# и что пароль достаточно надёжный, и сохраняет его в зашифрованном виде.
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        # Поля, которые увидит человек. Пароли форма добавит сама.
        fields = ('first_name', 'email')
        labels = {'first_name': 'Имя'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # По ТЗ имя обязательно (по умолчанию в Django оно необязательное)
        self.fields['first_name'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        # В модели User есть обязательное поле username (логин).
        # Вход у нас по почте, поэтому логином просто делаем почту.
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user
