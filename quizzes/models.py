# Совместно: модель базы данных
# Таблицы для тестов в конце уровня (Ф-9) и их результатов (Ф-10) — Нургуль
from django.conf import settings
from django.db import models


# Ф-9. Тест в конце уровня
class Quiz(models.Model):
    # Тест привязан к уровню курса (модель Level — у Фатимы в courses).
    # OneToOneField — у одного уровня ровно один тест.
    # on_delete=CASCADE — удалили уровень, удалился и его тест.
    level = models.OneToOneField('courses.Level', on_delete=models.CASCADE,
                                 related_name='quiz', verbose_name='Уровень')
    title = models.CharField('Название теста', max_length=200)
    # Порог сдачи в процентах. По ТЗ по умолчанию 80 %.
    pass_score = models.PositiveSmallIntegerField('Порог сдачи, %', default=80)

    def __str__(self):
        return self.title


# Вопрос теста
class Question(models.Model):
    # ForeignKey — у одного теста много вопросов.
    # related_name='questions' — потом можно писать quiz.questions.all()
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                             related_name='questions', verbose_name='Тест')
    text = models.TextField('Текст вопроса')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order']  # вопросы показываются по порядку

    def __str__(self):
        return self.text[:50]


# Вариант ответа на вопрос
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE,
                                 related_name='answers', verbose_name='Вопрос')
    text = models.CharField('Текст ответа', max_length=300)
    # Правильный ли это вариант. Это поле НЕ отправляется в браузер:
    # проверка идёт на сервере (Ф-9), поэтому ответ нельзя подсмотреть.
    is_correct = models.BooleanField('Правильный', default=False)

    def __str__(self):
        return self.text


# Ф-10. Попытка прохождения теста и её результат
class Attempt(models.Model):
    # Кто проходил. settings.AUTH_USER_MODEL — это наш accounts.User.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='attempts', verbose_name='Пользователь')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                             related_name='attempts', verbose_name='Тест')
    # Процент правильных ответов (0–100), считается на сервере.
    score = models.PositiveSmallIntegerField('Результат, %')
    # Сдан ли тест: score >= quiz.pass_score.
    passed = models.BooleanField('Сдан')
    # Дата и время попытки ставится автоматически.
    created_at = models.DateTimeField('Когда', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # сначала последние попытки

    def __str__(self):
        return f'{self.user} — {self.quiz}: {self.score}%'
