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


# Ф-13. Форма профиля: имя и аватар
# ModelForm — форма, которая строится по модели User и сама сохраняет
# изменения в базу. Почту здесь не меняем: по ней человек входит на сайт,
# поэтому в профиле она только показывается.
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'avatar')
        labels = {'first_name': 'Имя', 'avatar': 'Аватар'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Имя обязательно, как и при регистрации
        self.fields['first_name'].required = True
