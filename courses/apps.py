# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = 'courses'

    # ready() вызывается при запуске сайта: подключаем сигналы (Ф-12)
    def ready(self):
        from . import signals  # noqa: F401
