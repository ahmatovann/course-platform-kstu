# Ответственная: Нургуль (Ф-9, Ф-10)
# Автотесты теста и экрана результата. Запуск: python manage.py test quizzes
# Каждый метод test_... — один случай: что делает пользователь и что должно получиться.
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment, Lesson, LessonProgress, Level

from .models import Answer, Attempt, Question, Quiz
from .services import check_answers


class QuizTestBase(TestCase):
    # Общие данные для всех проверок: курс из двух уровней, у каждого тест
    def setUp(self):
        self.user = User.objects.create_user(
            username='u@test.kg', email='u@test.kg', first_name='Ученик', password='Pass12345!')
        self.course = Course.objects.create(title='Python', is_published=True)
        self.level1 = Level.objects.create(course=self.course, title='Первые шаги', order=1)
        self.level2 = Level.objects.create(course=self.course, title='Условия', order=2)
        self.lesson1 = Lesson.objects.create(level=self.level1, title='Урок 1', order=1)
        self.lesson2 = Lesson.objects.create(level=self.level2, title='Урок 2', order=1)

        # Тест 1-го уровня: 5 вопросов, у каждого правильный и неправильный вариант
        self.quiz = Quiz.objects.create(level=self.level1, title='Тест 1', pass_score=80)
        self.right = {}
        self.wrong = {}
        for i in range(5):
            q = Question.objects.create(quiz=self.quiz, text=f'Вопрос {i}', order=i)
            self.right[q.id] = Answer.objects.create(question=q, text='верно', is_correct=True).id
            self.wrong[q.id] = Answer.objects.create(question=q, text='неверно').id
        self.quiz2 = Quiz.objects.create(level=self.level2, title='Тест 2')
        q = Question.objects.create(quiz=self.quiz2, text='Вопрос')
        Answer.objects.create(question=q, text='да', is_correct=True)

        self.url = reverse('quizzes:quiz', args=[self.quiz.id])

    def login_enrolled(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.login(username='u@test.kg', password='Pass12345!')

    # Ответы формы: первые n вопросов верно, остальные неверно
    def answers(self, n_right):
        data = {}
        for i, qid in enumerate(self.right):
            data[f'question_{qid}'] = self.right[qid] if i < n_right else self.wrong[qid]
        return data


class CheckAnswersTests(QuizTestBase):
    # Ф-9. Проверка ответов на сервере (quizzes/services.py)
    def test_all_right(self):
        self.assertEqual(check_answers(self.quiz, self.right), (5, 5, 100))

    def test_all_wrong(self):
        self.assertEqual(check_answers(self.quiz, self.wrong), (0, 5, 0))

    def test_answer_from_other_question_is_wrong(self):
        # Подмена: в ответ на вопрос подставили номер правильного ответа ДРУГОГО вопроса
        ids = list(self.right)
        chosen = {ids[0]: self.right[ids[1]]}
        self.assertEqual(check_answers(self.quiz, chosen)[0], 0)

    def test_question_without_answers_is_not_counted(self):
        Question.objects.create(quiz=self.quiz, text='Пустой вопрос')
        self.assertEqual(check_answers(self.quiz, self.right), (5, 5, 100))


class QuizPageTests(QuizTestBase):
    def test_guest_goes_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_not_enrolled_is_redirected_to_course(self):
        self.client.login(username='u@test.kg', password='Pass12345!')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('courses:course_detail', args=[self.course.id]))

    def test_unpublished_course_gives_404(self):
        self.login_enrolled()
        self.course.is_published = False
        self.course.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_correct_answers_are_not_sent_to_browser(self):
        # п. 4.2 ТЗ: в странице теста нет признака правильного ответа
        self.login_enrolled()
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('is_correct', html)
        self.assertNotIn('correct', html.lower().replace('csrf', ''))

    def test_not_all_answered_shows_error_and_keeps_choices(self):
        self.login_enrolled()
        data = self.answers(5)
        first_key = next(iter(data))
        data.pop(first_key)
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Ответьте на все вопросы')
        self.assertEqual(Attempt.objects.count(), 0)
        self.assertContains(response, 'checked')

    def test_garbage_value_is_not_accepted(self):
        self.login_enrolled()
        data = self.answers(5)
        data[next(iter(data))] = 'abc'
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Ответьте на все вопросы')

    def test_pass_redirects_to_result(self):
        self.login_enrolled()
        response = self.client.post(self.url, self.answers(4))  # 4 из 5 = 80 %
        attempt = Attempt.objects.get()
        self.assertRedirects(response, reverse('quizzes:result', args=[attempt.id]))
        self.assertEqual((attempt.correct, attempt.total, attempt.score, attempt.passed),
                         (4, 5, 80, True))

    def test_below_threshold_is_failed(self):
        self.login_enrolled()
        self.client.post(self.url, self.answers(3))  # 60 %
        attempt = Attempt.objects.get()
        self.assertFalse(attempt.passed)

    def test_rounding_does_not_help_to_pass(self):
        # 79,5 % округлилось бы до 80 %, но тест сдан быть не должен
        self.quiz.pass_score = 80
        self.quiz.save()
        Question.objects.filter(quiz=self.quiz).delete()
        for i in range(200):
            q = Question.objects.create(quiz=self.quiz, text=str(i))
            Answer.objects.create(question=q, text='a', is_correct=True)
        chosen = {}
        for i, q in enumerate(self.quiz.questions.prefetch_related('answers')):
            answer = q.answers.first()
            chosen[f'question_{q.id}'] = answer.id if i < 159 else 999999
        self.login_enrolled()
        self.client.post(self.url, chosen)
        attempt = Attempt.objects.get()
        self.assertEqual(attempt.score, 80)
        self.assertFalse(attempt.passed)

    def test_admin_preview_does_not_save(self):
        admin = User.objects.create_superuser(email='a@test.kg', username='a', password='Admin12345!')
        self.client.force_login(admin)
        self.assertContains(self.client.get(self.url), 'Режим просмотра администратора')
        self.client.post(self.url, self.answers(5))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_closed_level_quiz_is_blocked(self):
        # Тест 2-го уровня нельзя пройти, пока 1-й уровень не пройден
        self.login_enrolled()
        response = self.client.get(reverse('quizzes:quiz', args=[self.quiz2.id]))
        self.assertRedirects(response, reverse('courses:course_detail', args=[self.course.id]))

    def test_quiz_without_questions(self):
        Question.objects.filter(quiz=self.quiz).delete()
        self.login_enrolled()
        self.assertContains(self.client.get(self.url), 'пока нет вопросов')
        self.client.post(self.url, {})
        self.assertEqual(Attempt.objects.count(), 0)


class ResultPageTests(QuizTestBase):
    def submit(self, n_right):
        self.client.post(self.url, self.answers(n_right))
        return Attempt.objects.latest('id')

    def test_failed_shows_retry(self):
        self.login_enrolled()
        attempt = self.submit(2)
        response = self.client.get(reverse('quizzes:result', args=[attempt.id]))
        self.assertContains(response, 'Тест не сдан')
        self.assertContains(response, 'Пройти заново')
        self.assertContains(response, 'Не хватило 40 %')

    def test_passed_but_lessons_not_watched(self):
        self.login_enrolled()
        attempt = self.submit(5)
        response = self.client.get(reverse('quizzes:result', args=[attempt.id]))
        self.assertContains(response, 'Тест сдан')
        self.assertContains(response, 'досмотрите все уроки')

    def test_passed_and_lessons_watched_opens_next_level(self):
        self.login_enrolled()
        LessonProgress.objects.create(user=self.user, lesson=self.lesson1)
        attempt = self.submit(5)
        response = self.client.get(reverse('quizzes:result', args=[attempt.id]))
        self.assertContains(response, 'открыт')
        self.assertContains(response, reverse('courses:lesson', args=[self.lesson2.id]))
        # и тест 2-го уровня теперь доступен
        self.assertEqual(self.client.get(reverse('quizzes:quiz', args=[self.quiz2.id])).status_code, 200)

    def test_someone_elses_result_is_404(self):
        self.login_enrolled()
        attempt = self.submit(5)
        User.objects.create_user(username='x@test.kg', email='x@test.kg', password='Pass12345!')
        self.client.login(username='x@test.kg', password='Pass12345!')
        self.assertEqual(self.client.get(reverse('quizzes:result', args=[attempt.id])).status_code, 404)

    def test_retry_after_fail_then_pass(self):
        self.login_enrolled()
        self.submit(1)
        attempt = self.submit(5)
        self.assertEqual(Attempt.objects.count(), 2)
        response = self.client.get(reverse('quizzes:result', args=[attempt.id]))
        self.assertContains(response, 'Мои попытки')
        self.assertContains(response, '20 %')

    def test_best_result_shown_on_quiz_page(self):
        self.login_enrolled()
        self.submit(5)
        self.submit(1)
        self.assertContains(self.client.get(self.url), 'Ваш лучший результат: <b>100 %</b>')
