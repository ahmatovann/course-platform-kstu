# Ответственная: Нургуль (Ф-14)
# Адрес страницы «Мой прогресс»: /progress/
from django.urls import path

from . import views

app_name = 'progress'

urlpatterns = [
    # Ф-14. Мой прогресс
    path('', views.my_progress, name='my_progress'),
]
