# Ответственная: Нургуль (Ф-1, Ф-13, доп. функция п. 4.1.3)
# Письма пользователю. Отдельный файл, чтобы views.py только принимал
# запрос и отдавал страницу, а «как отправить письмо» жило здесь.
import secrets
import string

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone


# Доп. функция: письмо «Ваш пароль изменён».
# Вызывается в двух местах: смена пароля в профиле (Ф-13)
# и восстановление пароля по ссылке из письма (Ф-3).
# Зачем: если пароль сменил не сам человек, он сразу узнает об этом.
def send_password_changed_email(request, user):
    # 1. Собираем данные для текста письма: имя, время, ссылка на сброс пароля.
    #    build_absolute_uri делает полную ссылку: http://127.0.0.1:8000/accounts/...
    context = {
        'user': user,
        'changed_at': timezone.localtime(),
        'reset_url': request.build_absolute_uri(reverse('password_reset')),
    }

    # 2. Текст письма берём из шаблона accounts/email/password_changed.txt
    message = render_to_string('accounts/email/password_changed.txt', context)

    # 3. Отправляем письмо на почту пользователя.
    #    Адрес отправителя — DEFAULT_FROM_EMAIL из settings.py.
    #    В режиме разработки письмо печатается в терминале, где запущен сервер.
    #    fail_silently=True — если почтовый сервер недоступен, пароль всё равно
    #    сменится, а сайт не покажет ошибку.
    send_mail(
        subject='Course Platform: ваш пароль изменён',
        message=message,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=True,
    )


# Ф-1. Пароль для нового пользователя.
# secrets — модуль Python для случайных значений, которые нельзя угадать.
# 10 символов из латинских букв и цифр.
def make_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(10))


# Ф-1. Письмо «Для вас создан аккаунт» с логином и паролем.
# Вызывается из админки (accounts/admin.py), когда администратор создаёт
# пользователя. Возвращает True, если письмо ушло, и False, если нет.
def send_account_email(request, user, password):
    # 1. Данные для текста письма: имя, логин, пароль и адрес страницы входа
    context = {
        'user': user,
        'password': password,
        'login_url': request.build_absolute_uri(reverse('login')),
    }
    # 2. Текст письма из шаблона accounts/email/account_created.txt
    message = render_to_string('accounts/email/account_created.txt', context)
    # 3. Отправляем. fail_silently=False — при ошибке Django сообщит о ней,
    #    чтобы админка могла показать предупреждение (см. accounts/admin.py).
    try:
        send_mail(
            subject='Course Platform: для вас создан аккаунт',
            message=message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        return False
    return True
