# Ответственная: Нургуль (Ф-9, Ф-10)
# Логика проверки теста. Вынесена из views.py в отдельный файл,
# чтобы её было легко объяснить и проверить отдельно.


# Ф-9. Проверка ответов на сервере
# quiz    — тест из базы
# chosen  — словарь {id вопроса: id выбранного ответа}, пришёл из формы
# Возвращает: сколько верных, сколько всего вопросов и процент.
def check_answers(quiz, chosen):
    questions = quiz.questions.all()
    total = questions.count()
    correct = 0

    for question in questions:
        answer_id = chosen.get(question.id)
        # Ищем выбранный вариант именно среди ответов ЭТОГО вопроса
        # и смотрим поле is_correct. Оно хранится только в базе
        # и в браузер не отправляется — подсмотреть его нельзя.
        if question.answers.filter(id=answer_id, is_correct=True).exists():
            correct += 1

    # Процент правильных ответов, округляем до целого.
    # Если вопросов нет — 0, чтобы не делить на ноль.
    score = round(correct * 100 / total) if total else 0
    return correct, total, score
