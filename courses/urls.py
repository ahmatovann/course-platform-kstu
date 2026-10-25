# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Адреса страниц приложения courses.
from django.urls import path

from . import views

# app_name — «фамилия» адресов: в шаблонах пишем {% url 'courses:catalog' %}
app_name = 'courses'

urlpatterns = [
    # Ф-4. Главная страница сайта — каталог курсов
    path('', views.catalog, name='catalog'),
]
