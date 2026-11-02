# Совместно: демо-данные для защиты проекта.
# Запуск: python manage.py demo
# Создаёт администратора, ученика и курс «Основы Python» из двух уровней
# с уроками и тестами — чтобы на защите сразу показать весь путь ученика
# (запись → уроки → тест → следующий уровень → сертификат) и панель администратора.
# Команду можно запускать сколько угодно раз: то, что уже есть, не дублируется.
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Course, Lesson, Level
from quizzes.models import Answer, Question, Quiz

ADMIN = ('admin@test.kg', 'Admin123!', 'Администратор')
STUDENT = ('student@test.kg', 'Student123!', 'Айжан')

# Уровень: название, уроки (название, описание), тест: [(вопрос, варианты, номер верного)]
COURSE = {
    'title': 'Основы Python',
    'description': 'Курс для начинающих: переменные, условия, циклы и функции.',
    'levels': [
        ('Первые шаги',
         [('Что такое Python', 'Знакомимся с языком и запускаем первую программу.'),
          ('Переменные', 'Как сохранить значение и вывести его на экран.')],
         [('Какая функция выводит текст на экран?', ['print', 'input', 'len'], 0),
          ('Сколько будет 2 + 3 * 2?', ['10', '8', '7'], 1),
          ('Как записать комментарий в Python?', ['// текст', '# текст', '<!-- текст -->'], 1)]),
        ('Условия и циклы',
         [('Условие if', 'Программа выбирает, что делать.'),
          ('Цикл for', 'Повторяем действие несколько раз.')],
         [('Какое слово начинает условие?', ['if', 'for', 'def'], 0),
          ('Сколько раз выполнится for i in range(3)?', ['2', '3', '4'], 1)]),
    ],
}


class Command(BaseCommand):
    help = 'Демо-данные для защиты: администратор, ученик и курс с уровнями и тестами'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # 1. Учётные записи. Пароль задаётся через set_password — в базе только хеш.
        for email, password, name, staff in [(*ADMIN, True), (*STUDENT, False)]:
            user, created = User.objects.get_or_create(
                email=email, defaults={'username': email, 'first_name': name})
            if created:
                user.is_staff = user.is_superuser = staff
                user.set_password(password)
                user.save()
            self.stdout.write(f'{"Создан" if created else "Уже есть"}: {email} / {password}')

        # 2. Курс с уровнями, уроками и тестами (если ещё нет).
        if Course.objects.filter(title=COURSE['title']).exists():
            self.stdout.write(f'Курс «{COURSE["title"]}» уже есть')
        else:
            course = Course.objects.create(title=COURSE['title'], is_published=True,
                                           description=COURSE['description'])
            for order, (title, lessons, questions) in enumerate(COURSE['levels'], 1):
                level = Level.objects.create(course=course, title=title, order=order)
                for n, (l_title, l_text) in enumerate(lessons, 1):
                    Lesson.objects.create(level=level, order=n, title=l_title, description=l_text)
                quiz = Quiz.objects.create(level=level, title=f'Тест: {title.lower()}')
                for n, (text, answers, right) in enumerate(questions, 1):
                    q = Question.objects.create(quiz=quiz, text=text, order=n)
                    for k, a in enumerate(answers):
                        Answer.objects.create(question=q, text=a, is_correct=(k == right))
            self.stdout.write(f'Создан курс «{COURSE["title"]}»: 2 уровня, 4 урока, 2 теста')

        # 3. Скрытый курс — чтобы показать А-1 (неопубликованный курс не виден в каталоге).
        _, created = Course.objects.get_or_create(
            title='Веб-разработка на Django (черновик)',
            defaults={'description': 'Курс ещё готовится, ученики его не видят.'})
        if created:
            self.stdout.write('Создан скрытый курс «Веб-разработка на Django (черновик)»')

        self.stdout.write(self.style.SUCCESS(
            'Готово. Запустите: python manage.py runserver → http://127.0.0.1:8000'))
