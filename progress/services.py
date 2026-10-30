# Ответственная: Нургуль (Ф-14). Логика прогресса по курсу.
# Здесь в одном месте посчитано всё, что нужно для «Моего прогресса» (Ф-14)
# и для экрана результата теста (Ф-10): сколько уроков просмотрено,
# сдан ли тест, какие уровни открыты и сколько процентов курса пройдено.
# Правило открытия уровней взято из п. 4.1 ТЗ: следующий уровень открывается,
# когда просмотрены все уроки текущего и тест сдан не ниже порога.
# Эту же функцию может использовать Фатима для Ф-11 (открытие уровней).
from courses.models import LessonProgress
from quizzes.models import Attempt


def course_progress(user, course):
    # 1. Уровни курса по порядку, сразу с уроками и тестом (меньше запросов к базе)
    levels = list(course.levels.order_by('order').prefetch_related('lessons'))

    # 2. Какие уроки этого курса пользователь уже посмотрел (Ф-8).
    #    set — множество номеров уроков: проверка «есть ли» работает мгновенно.
    watched_ids = set(
        LessonProgress.objects.filter(user=user, lesson__level__course=course)
        .values_list('lesson_id', flat=True)
    )

    # 3. Все попытки пользователя по тестам этого курса (новые первыми)
    attempts = list(
        Attempt.objects.filter(user=user, quiz__level__course=course)
        .select_related('quiz')
    )

    rows = []
    done_items = 0   # сколько «шагов» курса пройдено
    total_items = 0  # сколько «шагов» всего: каждый урок + каждый тест
    previous_complete = True  # первый уровень открыт всегда

    for level in levels:
        lessons = list(level.lessons.all())
        lessons_watched = sum(1 for lesson in lessons if lesson.id in watched_ids)

        # Тест уровня может ещё не быть создан администратором
        quiz = getattr(level, 'quiz', None)
        quiz_attempts = [a for a in attempts if quiz and a.quiz_id == quiz.id]
        best_score = max((a.score for a in quiz_attempts), default=None)
        test_passed = any(a.passed for a in quiz_attempts)

        # Уровень пройден: все уроки просмотрены и тест сдан
        # (если теста у уровня нет — достаточно уроков)
        lessons_done = lessons_watched == len(lessons)
        is_complete = lessons_done and (quiz is None or test_passed)

        # Уровень открыт, если все предыдущие уровни пройдены (п. 4.1 ТЗ)
        is_open = previous_complete
        previous_complete = previous_complete and is_complete

        total_items += len(lessons) + (1 if quiz else 0)
        done_items += lessons_watched + (1 if test_passed else 0)

        rows.append({
            'level': level,
            'lessons_total': len(lessons),
            'lessons_watched': lessons_watched,
            'first_lesson': lessons[0] if lessons else None,
            'quiz': quiz,
            'best_score': best_score,
            'attempts_count': len(quiz_attempts),
            'last_attempt': quiz_attempts[0] if quiz_attempts else None,
            'test_passed': test_passed,
            'is_open': is_open,
            'is_complete': is_complete,
        })

    # 4. Процент курса: пройденные шаги / все шаги. Если курс пустой — 0,
    #    чтобы не делить на ноль.
    percent = round(done_items * 100 / total_items) if total_items else 0

    return {
        'course': course,
        'levels': rows,
        'percent': percent,
        'done_items': done_items,
        'total_items': total_items,
        'is_completed': bool(rows) and all(row['is_complete'] for row in rows),
    }


# Состояние одного уровня (открыт ли, пройден ли) — для страницы теста
def level_state(user, level):
    progress = course_progress(user, level.course)
    for row in progress['levels']:
        if row['level'].id == level.id:
            return row, progress
    return None, progress
