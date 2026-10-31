# Совместно: модель базы данных
# Таблицы курсов, уровней, уроков и прохождения курса (совместная задача #1)
import secrets

from django.conf import settings
from django.db import models


# Ф-4, Ф-5. Курс
class Course(models.Model):
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    # Ф-4: в каталоге показываются только опубликованные курсы.
    # Пока курс не готов, администратор держит его неопубликованным.
    is_published = models.BooleanField('Опубликован', default=False)
    # auto_now_add=True — дата ставится сама при создании курса.
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'курс'
        verbose_name_plural = 'курсы'
        ordering = ['-created_at']  # сначала новые курсы

    def __str__(self):
        return self.title


# Ф-5, Ф-11. Уровень курса (на нём в конце стоит тест — модель Quiz у Нургуль)
class Level(models.Model):
    # ForeignKey — у одного курса много уровней.
    # on_delete=CASCADE — удалили курс, удалились и его уровни.
    # related_name='levels' — можно писать course.levels.all()
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='levels', verbose_name='Курс')
    title = models.CharField('Название', max_length=200)
    # Порядок нужен, чтобы уровни открывались по очереди (Ф-11).
    order = models.PositiveSmallIntegerField('Порядок', default=1)

    class Meta:
        verbose_name = 'уровень'
        verbose_name_plural = 'уровни'
        ordering = ['course', 'order']

    def __str__(self):
        return f'{self.course} — {self.title}'


# Ф-7. Урок внутри уровня
class Lesson(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE,
                              related_name='lessons', verbose_name='Уровень')
    title = models.CharField('Название', max_length=200)
    order = models.PositiveSmallIntegerField('Порядок', default=1)
    description = models.TextField('Описание', blank=True)
    # Видеофайл урока сохраняется в папку media/videos/.
    video = models.FileField('Видео', upload_to='videos/', blank=True)

    class Meta:
        verbose_name = 'урок'
        verbose_name_plural = 'уроки'
        ordering = ['level', 'order']

    def __str__(self):
        return self.title


# Ф-7. Файл к уроку: PDF, презентация или аудио
class Material(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name='materials', verbose_name='Урок')
    title = models.CharField('Название', max_length=200)
    file = models.FileField('Файл', upload_to='materials/')

    class Meta:
        verbose_name = 'материал'
        verbose_name_plural = 'материалы'

    def __str__(self):
        return self.title


# Ф-6. Запись пользователя на курс (курс попадает в «Мои курсы»)
class Enrollment(models.Model):
    # settings.AUTH_USER_MODEL — это пользователь Нургуль (accounts.User).
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='enrollments', verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='enrollments', verbose_name='Курс')
    enrolled_at = models.DateTimeField('Дата записи', auto_now_add=True)

    class Meta:
        verbose_name = 'запись на курс'
        verbose_name_plural = 'записи на курсы'
        # Нельзя записаться на один и тот же курс дважды.
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_enrollment'),
        ]

    def __str__(self):
        return f'{self.user} → {self.course}'


# Ф-8. Отметка, что урок просмотрен (после 90 % видео)
class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='lesson_progress', verbose_name='Пользователь')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name='progress', verbose_name='Урок')
    watched_at = models.DateTimeField('Когда просмотрен', auto_now_add=True)

    class Meta:
        verbose_name = 'просмотр урока'
        verbose_name_plural = 'просмотры уроков'
        # Один урок отмечается у пользователя только один раз.
        constraints = [
            models.UniqueConstraint(fields=['user', 'lesson'], name='unique_lesson_progress'),
        ]

    def __str__(self):
        return f'{self.user} — {self.lesson}'


# Ф-12. Сертификат о прохождении курса
class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='certificates', verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='certificates', verbose_name='Курс')
    issued_at = models.DateTimeField('Дата выдачи', auto_now_add=True)
    # Ф-12 (Э4). Номер сертификата, например CP-3F9A1C2B. По нему любой
    # (даже гость) может проверить, что сертификат настоящий: /certificate/check/
    # Номер случайный (модуль secrets), поэтому подобрать чужой нельзя.
    number = models.CharField('Номер', max_length=20, unique=True, null=True,
                              blank=True, editable=False)

    class Meta:
        verbose_name = 'сертификат'
        verbose_name_plural = 'сертификаты'
        # За один курс выдаётся один сертификат.
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_certificate'),
        ]

    # Номер ставится сам при первом сохранении сертификата
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = 'CP-' + secrets.token_hex(4).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Сертификат: {self.user} — {self.course}'
