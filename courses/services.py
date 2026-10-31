# Ответственная: Фатима (Ф-8, Ф-11, Ф-12) — этап Э4
# Логика прохождения курса в одном месте, чтобы views.py только
# принимал запрос и отдавал страницу.
#   Ф-8  — отметка «урок просмотрен»
#   Ф-11 — какие уровни открыты (по правилу п. 4.1 ТЗ)
#   Ф-12 — завершение курса и выдача сертификата
# Правило открытия уровней уже посчитано в progress/services.py
# (функция course_progress, часть Нургуль Ф-14). Мы берём его оттуда,
# чтобы урок, тест и «Мой прогресс» всегда считали одинаково.
from progress.services import course_progress

from .models import Certificate, Enrollment, LessonProgress


# Записан ли человек на курс (Ф-6)
def is_enrolled(user, course):
    return (user.is_authenticated
            and Enrollment.objects.filter(user=user, course=course).exists())


# Ф-11. «Программа» курса для шаблона: уровни по порядку, у каждого —
# открыт ли он, пройден ли, уроки с отметкой «просмотрен» и тест.
# Возвращает (program, progress): program — список для панели «Программа»,
# progress — полный подсчёт из course_progress (процент, курс пройден и т. д.).
def build_program(user, course):
    enrolled = is_enrolled(user, course)
    progress = course_progress(user, course) if enrolled else None

    # Какие уроки уже просмотрены — множество номеров уроков
    watched_ids = set()
    if enrolled:
        watched_ids = set(LessonProgress.objects.filter(
            user=user, lesson__level__course=course).values_list('lesson_id', flat=True))

    program = []
    if progress:
        rows = progress['levels']
    else:
        # Гость или не записан: состояние уровней не считаем, просто список
        rows = [{'level': level, 'is_open': False, 'is_complete': False,
                 'quiz': getattr(level, 'quiz', None), 'test_passed': False}
                for level in course.levels.order_by('order').prefetch_related('lessons')]

    for row in rows:
        level = row['level']
        program.append({
            'level': level,
            'is_open': row['is_open'],
            'is_complete': row['is_complete'],
            'quiz': row['quiz'],
            'test_passed': row['test_passed'],
            # У каждого урока — признак «просмотрен» (Ф-8)
            'lessons': [{'lesson': lesson, 'watched': lesson.id in watched_ids}
                        for lesson in level.lessons.all()],
        })
    return program, progress


# Ф-11. Открыт ли уровень урока для этого пользователя
def level_is_open(user, lesson):
    program, _ = build_program(user, lesson.level.course)
    for item in program:
        if item['level'].id == lesson.level_id:
            return item['is_open']
    return False


# Ф-7, Ф-11. Куда идти после урока: следующий урок уровня,
# потом тест уровня, потом первый урок следующего уровня.
# Возвращает (подпись кнопки, адрес) или (None, None), если дальше ничего нет.
def next_step(program, lesson):
    for index, item in enumerate(program):
        if item['level'].id != lesson.level_id:
            continue
        lessons = [entry['lesson'] for entry in item['lessons']]
        position = next(i for i, l in enumerate(lessons) if l.id == lesson.id)
        if position + 1 < len(lessons):
            following = lessons[position + 1]
            return f'Следующий урок: {following.title}', f'/lesson/{following.id}/'
        if item['quiz']:
            return 'Перейти к тесту уровня', f'/quizzes/{item["quiz"].id}/'
        if index + 1 < len(program) and program[index + 1]['lessons']:
            following = program[index + 1]['lessons'][0]['lesson']
            return 'Следующий уровень', f'/lesson/{following.id}/'
    return None, None


# Ф-12. Если курс пройден полностью — выдаём сертификат (один раз).
# Вызывается после отметки урока, после сдачи теста (courses/signals.py)
# и при открытии страницы курса — чтобы сертификат не потерялся.
def issue_certificate_if_completed(user, course):
    if not is_enrolled(user, course):
        return None
    if not course_progress(user, course)['is_completed']:
        return None
    # get_or_create — второй сертификат за тот же курс не создастся
    certificate, _ = Certificate.objects.get_or_create(user=user, course=course)
    return certificate


# Ф-8. Отметить урок просмотренным. get_or_create — повторная отметка
# не создаст дубль (в модели UniqueConstraint). Возвращает сертификат,
# если этим уроком курс оказался пройден.
def mark_lesson_watched(user, lesson):
    LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    return issue_certificate_if_completed(user, lesson.level.course)
