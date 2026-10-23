# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

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
# классах Django — они подключены в accounts/urls.py, свои функции не нужны.


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
            messages.success(request, 'Пароль изменён.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})
