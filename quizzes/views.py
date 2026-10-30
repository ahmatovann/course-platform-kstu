# Ответственная: Нургуль (Ф-9, Ф-10)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Enrollment
from progress.services import course_progress, level_state

from .models import Attempt, Quiz
from .services import check_answers, quiz_questions

# Ф-9 Прохождение теста — Нургуль
# Ф-10 Результат теста — Нургуль


# Ф-9. Прохождение теста в конце уровня
@login_required
def quiz_view(request, quiz_id):
    # 1. Находим тест опубликованного курса. Нет такого — страница 404.
    #    select_related сразу подтягивает уровень и курс одним запросом.
    quiz = get_object_or_404(
        Quiz.objects.select_related('level__course'),
        pk=quiz_id, level__course__is_published=True,
    )
    course = quiz.level.course

    # По ТЗ (п. 4.1.4) администратор тесты не проходит. Он может открыть
    # тест и посмотреть, как его видит ученик, но ответы не сохраняются.
    is_admin_preview = request.user.is_staff

    if not is_admin_preview:
        # 2. Тест доступен только тем, кто записан на курс (Ф-6)
        if not Enrollment.objects.filter(user=request.user, course=course).exists():
            messages.error(request, 'Сначала запишитесь на курс.')
            return redirect('courses:course_detail', pk=course.pk)

        # 3. Уровень должен быть открыт: все предыдущие уровни пройдены (п. 4.1 ТЗ)
        state, _ = level_state(request.user, quiz.level)
        if state and not state['is_open']:
            messages.error(request, 'Этот уровень ещё закрыт: сначала пройдите предыдущий.')
            return redirect('courses:course_detail', pk=course.pk)

    # Вопросы вместе с вариантами ответов (только вопросы, где есть варианты)
    questions = quiz_questions(quiz)

    # 4. Собираем ответы из формы: у каждого вопроса radio-кнопки
    #    с именем question_<id>, значение — id выбранного варианта.
    chosen = {}
    if request.method == 'POST':
        if is_admin_preview:
            messages.info(request, 'Вы администратор: это режим просмотра, ответы не сохраняются.')
            return redirect('quizzes:quiz', quiz_id=quiz.id)
        if not questions:
            messages.error(request, 'В этом тесте пока нет вопросов.')
            return redirect('quizzes:quiz', quiz_id=quiz.id)

        for question in questions:
            value = request.POST.get(f'question_{question.id}', '')
            # isdigit — отбрасываем мусор вместо номера ответа
            if value.isdigit():
                chosen[question.id] = int(value)

        # 5. Все ли вопросы отвечены? Если нет — показываем тест снова
        #    с уже выбранными ответами и сообщением.
        if len(chosen) < len(questions):
            messages.error(request, 'Ответьте на все вопросы.')
        else:
            # 6. Проверка на сервере (quizzes/services.py). Номер ответа от
            #    другого вопроса или несуществующий засчитывается как неверный.
            correct, total, score = check_answers(quiz, chosen)
            # 7. Сохраняем попытку: процент и сдан ли тест (порог задаёт админ)
            attempt = Attempt.objects.create(
                user=request.user,
                quiz=quiz,
                correct=correct,
                total=total,
                score=score,
                # Сравниваем точно, без округления: 79,5 % не должно считаться 80 %
                passed=correct * 100 >= quiz.pass_score * total,
            )
            # 8. Переходим на экран результата (Ф-10). Redirect нужен, чтобы
            #    при обновлении страницы (F5) тест не отправился второй раз.
            return redirect('quizzes:result', attempt_id=attempt.id)

    # Запоминаем у каждого вопроса выбранный ответ, чтобы при ошибке
    # «Ответьте на все вопросы» уже отмеченные варианты не сбрасывались
    for question in questions:
        question.chosen_id = chosen.get(question.id)

    # Лучший прошлый результат — показываем над тестом
    best_attempt = None
    if not is_admin_preview:
        best_attempt = (Attempt.objects.filter(user=request.user, quiz=quiz)
                        .order_by('-score', '-created_at').first())

    return render(request, 'quizzes/quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'is_admin_preview': is_admin_preview,
        'best_attempt': best_attempt,
    })


# Ф-10. Экран результата: процент, сдан или нет, пересдача, следующий уровень
@login_required
def result_view(request, attempt_id):
    # 1. Только СВОЯ попытка: чужую по номеру в адресе открыть нельзя (404)
    attempt = get_object_or_404(
        Attempt.objects.select_related('quiz__level__course'),
        pk=attempt_id, user=request.user,
    )
    quiz = attempt.quiz
    course = quiz.level.course

    # 2. Прогресс по курсу (progress/services.py): какие уровни открыты
    progress = course_progress(request.user, course)
    rows = progress['levels']
    index = next((i for i, row in enumerate(rows) if row['level'].id == quiz.level_id), None)
    current = rows[index] if index is not None else None
    next_row = rows[index + 1] if index is not None and index + 1 < len(rows) else None

    # 3. История попыток по этому тесту (последние 10)
    history = Attempt.objects.filter(user=request.user, quiz=quiz)[:10]

    return render(request, 'quizzes/result.html', {
        'attempt': attempt,
        'quiz': quiz,
        'course': course,
        'current': current,
        'next_row': next_row,
        'progress': progress,
        # Сколько процентов не хватило до порога (для неудачной попытки)
        'missing': max(quiz.pass_score - attempt.score, 0),
        'history': history,
    })
