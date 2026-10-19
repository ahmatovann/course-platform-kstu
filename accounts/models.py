# Совместно: модель базы данных
from django.db import models
# AbstractUser — встроенный в Django «заготовленный» пользователь.
# В нём уже есть: username (логин), password (пароль хранится
# в зашифрованном виде), first_name, last_name, is_active и др.
# Мы наследуемся от него и добавляем только то, чего не хватает по ТЗ.
from django.contrib.auth.models import AbstractUser


# Ф-1, Ф-2, Ф-13. Пользователь платформы — Нургуль
class User(AbstractUser):
    # Почта пользователя (Ф-1, Ф-2).
    # unique=True — в базе не может быть двух аккаунтов с одной почтой,
    # потому что именно по почте человек входит на сайт.
    email = models.EmailField('Почта', unique=True)

    # Аватар для личного кабинета (Ф-13).
    # upload_to='avatars/' — картинки сохраняются в папку media/avatars/.
    # blank=True — поле необязательное: можно жить и без аватара.
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)

    # По умолчанию Django входит по логину (username).
    # Эта строка говорит: входить по почте (Ф-2 «Авторизация по e-mail»).
    USERNAME_FIELD = 'email'

    # Какие поля ещё спросить при создании администратора
    # командой createsuperuser (почта и пароль спрашиваются всегда).
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # Как пользователь отображается в админке и списках — по почте.
        return self.email
