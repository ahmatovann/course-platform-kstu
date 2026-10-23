# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
# Адреса для входа, регистрации и восстановления пароля: /accounts/...
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Ф-1. Регистрация — своя функция register в accounts/views.py
    path('register/', views.register, name='register'),

    # Ф-2. Вход и выход — готовые классы Django, указываем только свой шаблон.
    # LoginView сам проверяет почту и пароль и запускает сессию.
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    # LogoutView завершает сессию. Работает только по POST (кнопка-форма).
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Ф-3. Восстановление пароля — 4 шага:
    # 1) ввести почту → 2) «письмо отправлено» →
    # 3) ссылка из письма: ввести новый пароль → 4) «пароль изменён»
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Ф-13. Профиль и смена пароля — свои функции в accounts/views.py
    path('profile/', views.profile, name='profile'),
    path('password-change/', views.password_change, name='password_change'),
]
