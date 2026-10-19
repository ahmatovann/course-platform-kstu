# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegisterForm

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
