# Ответственная: Нургуль (Ф-9, Ф-10)
# Адреса тестов: /quizzes/...
from django.urls import path

from . import views

# app_name — в шаблонах пишем {% url 'quizzes:quiz' quiz.id %}
app_name = 'quizzes'

urlpatterns = [
    # Ф-9. Тест уровня, например /quizzes/1/
    path('<int:quiz_id>/', views.quiz_view, name='quiz'),
    # Ф-10. Результат попытки, например /quizzes/result/5/
    path('result/<int:attempt_id>/', views.result_view, name='result'),
]
