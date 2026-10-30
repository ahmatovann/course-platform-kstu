# Совместно: команда для показа базы данных на паре.
# Запуск: python manage.py dbinfo
# Показывает, где лежит файл базы, сколько он весит, какие в нём таблицы
# и сколько в каждой записей, а также что пароли хранятся только хешем (п. 4.2 ТЗ).
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Где хранится база данных и что в ней лежит'

    def handle(self, *args, **options):
        db = settings.DATABASES['default']

        # 1. Какая база и где её файл (берётся из config/settings.py → DATABASES)
        self.stdout.write('=== База данных проекта ===')
        self.stdout.write(f'Тип базы:   {db["ENGINE"].split(".")[-1]}')
        path = Path(db['NAME']).resolve()
        self.stdout.write(f'Файл базы:  {path}')
        if path.exists():
            self.stdout.write(f'Размер:     {path.stat().st_size / 1024:.0f} КБ')
        self.stdout.write('Настройка:  config/settings.py → DATABASES')
        self.stdout.write('В Git:      не попадает (строка db.sqlite3 в .gitignore)')

        # 2. Все таблицы и сколько в каждой строк.
        #    connection.introspection — встроенный в Django способ «заглянуть» в базу.
        self.stdout.write('')
        self.stdout.write('=== Таблицы (наши приложения) ===')
        tables = connection.introspection.table_names()
        ours = [t for t in tables if t.split('_')[0] in ('accounts', 'courses', 'quizzes')]
        with connection.cursor() as cursor:
            for table in ours:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cursor.fetchone()[0]
                self.stdout.write(f'  {table:<32} записей: {count}')
        self.stdout.write(f'Всего таблиц в базе: {len(tables)} (остальные — служебные таблицы Django)')

        # 3. Доказательство п. 4.2 ТЗ: в базе не пароль, а его хеш
        user = get_user_model().objects.order_by('pk').first()
        if user:
            self.stdout.write('')
            self.stdout.write('=== Как хранится пароль (п. 4.2 ТЗ) ===')
            self.stdout.write(f'Пользователь: {user.email}')
            self.stdout.write(f'В базе:       {user.password[:45]}...')
            self.stdout.write('Это хеш: по нему можно проверить пароль, но нельзя его узнать.')

        # 4. Где лежат загруженные файлы (видео, аватары)
        self.stdout.write('')
        self.stdout.write(f'Видео и аватары: {Path(settings.MEDIA_ROOT).resolve()} (в Git тоже не попадают)')
