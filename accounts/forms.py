# Ответственная: Нургуль (Ф-13)
# Форма создания пользователя администратором (Ф-1) — в accounts/admin.py
from django import forms

from .models import User


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
        # Имя обязательно
        self.fields['first_name'].required = True
