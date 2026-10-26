# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Адреса страниц приложения courses.
from django.urls import path

from . import views

# app_name — «фамилия» адресов: в шаблонах пишем {% url 'courses:catalog' %}
app_name = 'courses'

urlpatterns = [
    # Ф-4. Главная страница сайта — каталог курсов
    path('', views.catalog, name='catalog'),
    # Ф-5. Карточка курса, например /course/1/
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    # Ф-6. Запись на курс (кнопка «Записаться») и список «Мои курсы»
    path('course/<int:pk>/enroll/', views.enroll, name='enroll'),
    path('my-courses/', views.my_courses, name='my_courses'),
    # Ф-7. Страница урока, например /lesson/3/
    path('lesson/<int:pk>/', views.lesson_view, name='lesson'),
]
