# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse

from .emails import send_password_changed_email
from .forms import ProfileForm

# Ф-1 Получение доступа (аккаунт создаёт админ) — Нургуль
# Ф-2 Вход и выход — Нургуль
# Ф-3 Восстановление пароля — Нургуль
# Ф-13 Профиль — Нургуль


# Ф-1. Самостоятельной регистрации нет (по ТЗ): аккаунт создаёт
# администратор в админке, логин и пароль приходят на почту.
# Код этого — в accounts/admin.py и accounts/emails.py.


# Ф-2. Вход. Берём готовый класс Django LoginView (он сам проверяет почту
# и пароль и запускает сессию) и меняем только одно — куда попасть после входа.
class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        # is_staff — у администратора True, у обычного пользователя False.
        # По ТЗ (Э1) администратор попадает в панель администратора,
        # обучающийся — в раздел «Мои курсы».
        if self.request.user.is_staff:
            return '/admin/'
        return reverse('courses:my_courses')


# Ф-2 (выход) и Ф-3 (восстановление пароля) сделаны на готовых
# классах Django — они подключены в accounts/urls.py.


# Ф-3, шаг 3 + доп. функция. Новый пароль по ссылке из письма.
# Берём готовый класс Django PasswordResetConfirmView и добавляем одно:
# после успешной смены пароля отправляем письмо «Ваш пароль изменён».
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'

    # form_valid вызывается, когда новый пароль введён правильно (два раза одинаково).
    def form_valid(self, form):
        # super() — сначала Django сам сохраняет новый пароль
        response = super().form_valid(form)
        # form.user — пользователь, которому меняли пароль
        send_password_changed_email(self.request, form.user)
        return response


# Ф-13. Профиль: личные данные (имя, почта) и аватар
# @login_required — страница только для вошедших. Если человек не вошёл,
# Django отправит его на страницу входа (LOGIN_URL в settings.py).
@login_required
def profile(request):
    if request.method == 'POST':
        # 1. Человек нажал «Сохранить».
        #    request.FILES — загруженная картинка аватара.
        #    instance=request.user — меняем именно текущего пользователя,
        #    а не создаём нового.
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        # 2. Проверяем: имя не пустое, файл действительно картинка
        if form.is_valid():
            # 3. Сохраняем в базу, картинка ложится в media/avatars/
            form.save()
            # 4. Короткое сообщение вверху страницы и снова открываем профиль
            messages.success(request, 'Профиль сохранён.')
            return redirect('profile')
    else:
        # Просто открыли страницу — форма уже заполнена текущими данными
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


# Ф-13. Смена пароля из профиля
@login_required
def password_change(request):
    if request.method == 'POST':
        # PasswordChangeForm — готовая форма Django: старый пароль
        # и новый пароль два раза. Она проверяет, что старый пароль верный.
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # После смены пароля Django завершил бы сессию.
            # update_session_auth_hash оставляет человека в аккаунте.
            update_session_auth_hash(request, user)
            # Доп. функция: письмо на почту «Ваш пароль изменён» (accounts/emails.py)
            send_password_changed_email(request, user)
            messages.success(request, 'Пароль изменён. Мы отправили письмо на вашу почту.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})
