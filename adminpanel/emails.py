# Ответственная: Фатима (А-5) — этап Э5
# Письмо «Вам выдан новый пароль». Построено так же, как письма Нургуль
# в accounts/emails.py: текст в шаблоне, отправка через send_mail.
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def send_new_password_email(request, user, password):
    message = render_to_string('adminpanel/email/new_password.txt', {
        'user': user,
        'password': password,
        'login_url': request.build_absolute_uri(reverse('login')),
    })
    # fail_silently=False + try: если почта не работает, админ увидит пароль на экране
    try:
        send_mail(
            subject='Course Platform: вам выдан новый пароль',
            message=message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        return False
    return True
