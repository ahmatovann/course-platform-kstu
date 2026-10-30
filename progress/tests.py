# Ответственная: Нургуль (Ф-14)
# Автотесты «Моего прогресса». Запуск: python manage.py test progress
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment, Lesson, LessonProgress, Level
from quizzes.models import Answer, Attempt, Question, Quiz

from .services import course_progress


class ProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='u@test.kg', email='u@test.kg', password='Pass12345!')
        self.course = Course.objects.create(title='Python', is_published=True)
        self.l1 = Level.objects.create(course=self.course, title='Уровень 1', order=1)
        self.l2 = Level.objects.create(course=self.course, title='Уровень 2', order=2)
        self.a = Lesson.objects.create(level=self.l1, title='A', order=1)
        self.b = Lesson.objects.create(level=self.l1, title='B', order=2)
        self.c = Lesson.objects.create(level=self.l2, title='C', order=1)
        self.q1 = Quiz.objects.create(level=self.l1, title='Тест 1')
        self.q2 = Quiz.objects.create(level=self.l2, title='Тест 2')
        for quiz in (self.q1, self.q2):
            q = Question.objects.create(quiz=quiz, text='?')
            Answer.objects.create(question=q, text='да', is_correct=True)

    # --- логика подсчёта (progress/services.py) ---
    def test_nothing_done(self):
        p = course_progress(self.user, self.course)
        self.assertEqual((p['percent'], p['done_items'], p['total_items']), (0, 0, 5))
        self.assertTrue(p['levels'][0]['is_open'])
        self.assertFalse(p['levels'][1]['is_open'])

    def test_lessons_and_test_count(self):
        LessonProgress.objects.create(user=self.user, lesson=self.a)
        Attempt.objects.create(user=self.user, quiz=self.q1, score=100, passed=True)
        p = course_progress(self.user, self.course)
        self.assertEqual(p['percent'], 40)  # 2 из 5
        self.assertFalse(p['levels'][1]['is_open'])  # урок B не просмотрен

    def test_level_opens_after_lessons_and_test(self):
        LessonProgress.objects.create(user=self.user, lesson=self.a)
        LessonProgress.objects.create(user=self.user, lesson=self.b)
        Attempt.objects.create(user=self.user, quiz=self.q1, score=100, passed=True)
        p = course_progress(self.user, self.course)
        self.assertTrue(p['levels'][0]['is_complete'])
        self.assertTrue(p['levels'][1]['is_open'])

    def test_failed_attempts_do_not_count(self):
        Attempt.objects.create(user=self.user, quiz=self.q1, score=40, passed=False)
        row = course_progress(self.user, self.course)['levels'][0]
        self.assertEqual((row['best_score'], row['test_passed'], row['attempts_count']), (40, False, 1))

    def test_best_score_and_pass_kept_after_worse_try(self):
        Attempt.objects.create(user=self.user, quiz=self.q1, score=100, passed=True)
        Attempt.objects.create(user=self.user, quiz=self.q1, score=20, passed=False)
        row = course_progress(self.user, self.course)['levels'][0]
        self.assertEqual((row['best_score'], row['test_passed']), (100, True))

    def test_course_completed(self):
        for lesson in (self.a, self.b, self.c):
            LessonProgress.objects.create(user=self.user, lesson=lesson)
        for quiz in (self.q1, self.q2):
            Attempt.objects.create(user=self.user, quiz=quiz, score=100, passed=True)
        p = course_progress(self.user, self.course)
        self.assertEqual(p['percent'], 100)
        self.assertTrue(p['is_completed'])

    def test_other_users_progress_not_mixed(self):
        other = User.objects.create_user(username='o@test.kg', email='o@test.kg', password='x')
        LessonProgress.objects.create(user=other, lesson=self.a)
        Attempt.objects.create(user=other, quiz=self.q1, score=100, passed=True)
        self.assertEqual(course_progress(self.user, self.course)['percent'], 0)

    def test_empty_course(self):
        empty = Course.objects.create(title='Пустой', is_published=True)
        p = course_progress(self.user, empty)
        self.assertEqual((p['percent'], p['is_completed']), (0, False))

    def test_level_without_quiz(self):
        level = Level.objects.create(course=self.course, title='Без теста', order=3)
        lesson = Lesson.objects.create(level=level, title='D')
        LessonProgress.objects.create(user=self.user, lesson=lesson)
        row = course_progress(self.user, self.course)['levels'][2]
        self.assertTrue(row['is_complete'])

    # --- страница /progress/ ---
    def test_guest_goes_to_login(self):
        url = reverse('progress:my_progress')
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_admin_has_no_progress_page(self):
        admin = User.objects.create_superuser(email='a@test.kg', username='a', password='x')
        self.client.force_login(admin)
        response = self.client.get(reverse('progress:my_progress'))
        self.assertEqual(response.status_code, 302)

    def test_page_without_courses(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('progress:my_progress')), 'ещё не записались')

    def test_page_shows_course_percent_and_levels(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        LessonProgress.objects.create(user=self.user, lesson=self.a)
        self.client.force_login(self.user)
        response = self.client.get(reverse('progress:my_progress'))
        self.assertContains(response, 'Python')
        self.assertContains(response, '20 %')
        self.assertContains(response, 'Открыт')
        self.assertContains(response, 'Закрыт')

    def test_menu_link_only_for_students(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/'), 'Мой прогресс')
