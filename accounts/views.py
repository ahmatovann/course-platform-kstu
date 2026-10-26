# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

from .emails import send_password_changed_email
from .forms import ProfileForm, RegisterForm

# Ф-1 Регистрация — Нургуль
# Ф-2 Вход и выход — Нургуль
# Ф-3 Восстановление пароля — Нургуль
# Ф-13 Профиль — Нургуль


# Ф-1. Регистрация: создание учётной записи по имени, почте и паролю
def register(request):
    # Уже вошедшему пользователю регистрация не нужна — отправляем в каталог
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        # 1. Человек нажал «Зарегистрироваться» — заполняем форму его данными
        form = RegisterForm(request.POST)
        # 2. is_valid() проверяет: почта не занята, пароли совпадают, пароль надёжный
        if form.is_valid():
            # 3. Сохраняем пользователя в базу (пароль — в виде хеша)
            user = form.save()
            # 4. Сразу входим под новым аккаунтом и отправляем в каталог
            login(request, user)
            return redirect('/')
    else:
        # Человек просто открыл страницу — показываем пустую форму
        form = RegisterForm()

    # Если были ошибки, форма покажется снова уже с сообщениями об ошибках
    return render(request, 'accounts/register.html', {'form': form})


# Ф-2 (вход и выход) и Ф-3 (восстановление пароля) сделаны на готовых
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
