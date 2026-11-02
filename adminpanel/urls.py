# Ответственная: Фатима (А-1 – А-6) — этап Э5
# Адреса панели администратора: /panel/...
from django.urls import path

from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Обзор
    path('', views.dashboard, name='dashboard'),
    # А-1. Курсы
    path('courses/', views.course_list, name='course_list'),
    path('courses/new/', views.course_form, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_form, name='course_edit'),
    path('courses/<int:pk>/toggle/', views.course_toggle, name='course_toggle'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    # А-2. Уровни
    path('courses/<int:course_pk>/levels/new/', views.level_form, name='level_create'),
    path('levels/<int:pk>/edit/', views.level_form, name='level_edit'),
    path('levels/<int:pk>/delete/', views.level_delete, name='level_delete'),
    # А-3. Уроки и материалы
    path('levels/<int:level_pk>/lessons/new/', views.lesson_form, name='lesson_create'),
    path('lessons/<int:pk>/', views.lesson_form, name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lessons/<int:lesson_pk>/materials/add/', views.material_add, name='material_add'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    # А-4. Конструктор тестов
    path('levels/<int:level_pk>/quiz/', views.quiz_edit, name='quiz_edit'),
    path('levels/<int:level_pk>/questions/new/', views.question_form, name='question_create'),
    path('levels/<int:level_pk>/questions/<int:pk>/', views.question_form, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    # А-5. Пользователи
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
    path('users/<int:pk>/password/', views.user_new_password, name='user_new_password'),
    # А-6. Прогресс
    path('users/<int:pk>/progress/', views.user_progress, name='user_progress'),
    path('progress/', views.progress_overview, name='progress'),
    # Сверх ТЗ: администратор записывает ученика на курс или отчисляет
    path('enrollments/add/', views.enrollment_add, name='enrollment_add'),
    path('enrollments/<int:pk>/remove/', views.enrollment_remove, name='enrollment_remove'),
]
