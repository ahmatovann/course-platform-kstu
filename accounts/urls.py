# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
# Адреса для входа и восстановления пароля: /accounts/...
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Ф-1. Регистрации нет: аккаунт создаёт администратор (accounts/admin.py)

    # Ф-2. Вход — свой класс LoginView из accounts/views.py:
    # после входа админ попадает в панель администратора, обучающийся — в «Мои курсы».
    path('login/', views.LoginView.as_view(), name='login'),
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
    # Шаг 3 — свой класс из accounts/views.py: он ещё шлёт письмо «Ваш пароль изменён»
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Ф-13. Профиль и смена пароля — свои функции в accounts/views.py
    path('profile/', views.profile, name='profile'),
    path('password-change/', views.password_change, name='password_change'),
]
