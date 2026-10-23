# Ответственная: Нургуль (Ф-9, Ф-10)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Enrollment

from .models import Attempt, Quiz
from .services import check_answers

# Ф-9 Прохождение теста — Нургуль
# Ф-10 Результат теста — Нургуль (этап Э4)


# Ф-9. Прохождение теста в конце уровня
@login_required
def quiz_view(request, quiz_id):
    # 1. Находим тест. Если такого нет — страница 404.
    #    select_related сразу подтягивает уровень и курс одним запросом.
    quiz = get_object_or_404(Quiz.objects.select_related('level__course'), pk=quiz_id)
    course = quiz.level.course

    # 2. Тест доступен только тем, кто записан на курс (Ф-6)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, 'Сначала запишитесь на курс.')
        return redirect('/')

    # Вопросы вместе с вариантами ответов (prefetch_related — без лишних запросов)
    questions = list(quiz.questions.prefetch_related('answers'))

    # 3. Собираем ответы из формы: у каждого вопроса radio-кнопки
    #    с именем question_<id>, значение — id выбранного варианта.
    chosen = {}
    if request.method == 'POST':
        for question in questions:
            value = request.POST.get(f'question_{question.id}')
            if value and value.isdigit():
                chosen[question.id] = int(value)

        # 4. Все ли вопросы отвечены? Если нет — показываем тест снова
        #    с уже выбранными ответами и сообщением.
        if len(chosen) < len(questions):
            messages.error(request, 'Ответьте на все вопросы.')
        else:
            # 5. Проверка на сервере (quizzes/services.py)
            correct, total, score = check_answers(quiz, chosen)
            # 6. Сохраняем попытку: процент и сдан ли тест (порог 80 %)
            Attempt.objects.create(
                user=request.user,
                quiz=quiz,
                score=score,
                passed=score >= quiz.pass_score,
            )
            # Пока выводим короткое сообщение. Отдельный экран результата
            # с пересдачей и открытием уровня (Ф-10) — этап Э4.
            messages.success(
                request,
                f'Ответы проверены на сервере: верно {correct} из {total} ({score} %).',
            )
            return redirect('quizzes:quiz', quiz_id=quiz.id)

    # Запоминаем у каждого вопроса выбранный ответ, чтобы при ошибке
    # «Ответьте на все вопросы» уже отмеченные варианты не сбрасывались
    for question in questions:
        question.chosen_id = chosen.get(question.id)

    return render(request, 'quizzes/quiz.html', {
        'quiz': quiz,
        'questions': questions,
    })
