# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Автотесты каталога, курса, урока, отметки о просмотре, открытия уровней
# и сертификата. Запуск: python manage.py test courses
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from quizzes.models import Answer, Attempt, Question, Quiz

from .models import Certificate, Course, Enrollment, Lesson, LessonProgress, Level, Material


class CourseTestBase(TestCase):
    # Курс из двух уровней: в 1-м два урока и тест, во 2-м один урок и тест
    def setUp(self):
        self.user = User.objects.create_user(
            username='u@test.kg', email='u@test.kg', first_name='Айгерим', password='Pass12345!')
        self.course = Course.objects.create(title='Python', description='Курс', is_published=True)
        self.hidden = Course.objects.create(title='Черновик', is_published=False)
        self.l1 = Level.objects.create(course=self.course, title='Старт', order=1)
        self.l2 = Level.objects.create(course=self.course, title='Условия', order=2)
        self.a = Lesson.objects.create(level=self.l1, title='Урок A', order=1,
                                       video=SimpleUploadedFile('v.mp4', b'0', 'video/mp4'))
        self.b = Lesson.objects.create(level=self.l1, title='Урок B', order=2)
        self.c = Lesson.objects.create(level=self.l2, title='Урок C', order=1)
        self.q1 = Quiz.objects.create(level=self.l1, title='Тест 1')
        self.q2 = Quiz.objects.create(level=self.l2, title='Тест 2')
        for quiz in (self.q1, self.q2):
            question = Question.objects.create(quiz=quiz, text='?')
            Answer.objects.create(question=question, text='да', is_correct=True)

    def enroll_and_login(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.force_login(self.user)

    def watch(self, lesson):
        return self.client.post(reverse('courses:lesson_watched', args=[lesson.id]),
                                HTTP_X_REQUESTED_WITH='fetch')

    def pass_quiz(self, quiz):
        Attempt.objects.create(user=self.user, quiz=quiz, correct=1, total=1, score=100, passed=True)


class CatalogAndCourseTests(CourseTestBase):
    # Ф-4. Каталог и поиск
    def test_catalog_shows_only_published(self):
        html = self.client.get('/').content.decode()
        self.assertIn('Python', html)
        self.assertNotIn('Черновик', html)

    def test_search(self):
        self.assertContains(self.client.get('/?q=pyth'), 'Python')
        self.assertNotContains(self.client.get('/?q=zzz'), 'Урок A')

    # Ф-5. Карточка курса
    def test_course_page_and_hidden_404(self):
        self.assertContains(self.client.get(f'/course/{self.course.id}/'), 'Урок C')
        self.assertEqual(self.client.get(f'/course/{self.hidden.id}/').status_code, 404)

    # Ф-6. Запись без дубля
    def test_enroll_once(self):
        self.client.force_login(self.user)
        url = reverse('courses:enroll', args=[self.course.id])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Enrollment.objects.filter(user=self.user).count(), 1)

    def test_admin_does_not_enroll(self):
        admin = User.objects.create_superuser(email='a@test.kg', username='a', password='x')
        self.client.force_login(admin)
        self.client.post(reverse('courses:enroll', args=[self.course.id]))
        self.assertFalse(Enrollment.objects.filter(user=admin).exists())


class LessonTests(CourseTestBase):
    # Ф-7. Урок: видео, описание, файлы
    def test_lesson_needs_enrollment(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('courses:lesson', args=[self.a.id]))
        self.assertRedirects(response, reverse('courses:course_detail', args=[self.course.id]))

    def test_lesson_page_video_and_materials(self):
        Material.objects.create(lesson=self.a, title='PDF', file=SimpleUploadedFile('a.pdf', b'%', 'application/pdf'))
        Material.objects.create(lesson=self.a, title='MP3', file=SimpleUploadedFile('a.mp3', b'I', 'audio/mpeg'))
        self.enroll_and_login()
        html = self.client.get(reverse('courses:lesson', args=[self.a.id])).content.decode()
        self.assertIn('<video', html)
        self.assertIn('Открыть PDF', html)
        self.assertIn('<audio', html)
        self.assertIn('data-watched-url', html)  # скрипт 90 % подключён

    # Ф-11. Урок закрытого уровня не открывается даже по адресу
    def test_closed_level_lesson_blocked(self):
        self.enroll_and_login()
        response = self.client.get(reverse('courses:lesson', args=[self.c.id]))
        self.assertRedirects(response, reverse('courses:course_detail', args=[self.course.id]))

    def test_next_step_buttons(self):
        self.enroll_and_login()
        self.assertContains(self.client.get(reverse('courses:lesson', args=[self.a.id])), 'Следующий урок: Урок B')
        self.assertContains(self.client.get(reverse('courses:lesson', args=[self.b.id])), 'Перейти к тесту уровня')

    def test_admin_preview_any_lesson(self):
        admin = User.objects.create_superuser(email='a@test.kg', username='a', password='x')
        self.client.force_login(admin)
        response = self.client.get(reverse('courses:lesson', args=[self.c.id]))
        self.assertContains(response, 'Режим просмотра администратора')
        self.assertNotContains(response, 'data-watched-url')


class WatchedTests(CourseTestBase):
    # Ф-8. Отметка «просмотрен»
    def test_mark_watched(self):
        self.enroll_and_login()
        response = self.watch(self.a)
        self.assertEqual(response.json()['ok'], True)
        self.assertTrue(LessonProgress.objects.filter(user=self.user, lesson=self.a).exists())

    def test_mark_twice_no_duplicate(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.watch(self.a)
        self.assertEqual(LessonProgress.objects.filter(user=self.user).count(), 1)

    def test_get_not_allowed(self):
        self.enroll_and_login()
        response = self.client.get(reverse('courses:lesson_watched', args=[self.a.id]))
        self.assertEqual(response.status_code, 405)

    def test_not_enrolled_cannot_mark(self):
        self.client.force_login(self.user)
        self.assertEqual(self.watch(self.a).status_code, 403)
        self.assertFalse(LessonProgress.objects.exists())

    def test_closed_level_cannot_mark(self):
        self.enroll_and_login()
        self.assertEqual(self.watch(self.c).status_code, 403)

    def test_button_for_lesson_without_video(self):
        self.enroll_and_login()
        self.assertContains(self.client.get(reverse('courses:lesson', args=[self.b.id])), 'Отметить урок как изученный')
        response = self.client.post(reverse('courses:lesson_watched', args=[self.b.id]))
        self.assertRedirects(response, reverse('courses:lesson', args=[self.b.id]))
        self.assertTrue(LessonProgress.objects.filter(lesson=self.b).exists())

    def test_watched_badge_after_mark(self):
        self.enroll_and_login()
        self.watch(self.a)
        html = self.client.get(reverse('courses:lesson', args=[self.a.id])).content.decode()
        self.assertIn('✓ Урок просмотрен', html)
        self.assertNotIn('data-watched-url', html)


class LevelOpeningTests(CourseTestBase):
    # Ф-11. Следующий уровень открывается сам: уроки просмотрены + тест сдан
    def test_only_test_not_enough(self):
        self.enroll_and_login()
        self.pass_quiz(self.q1)
        self.assertEqual(self.client.get(reverse('courses:lesson', args=[self.c.id])).status_code, 302)

    def test_only_lessons_not_enough(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.watch(self.b)
        self.assertEqual(self.client.get(reverse('courses:lesson', args=[self.c.id])).status_code, 302)

    def test_lessons_and_test_open_next_level(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.watch(self.b)
        self.pass_quiz(self.q1)
        self.assertEqual(self.client.get(reverse('courses:lesson', args=[self.c.id])).status_code, 200)
        self.assertContains(self.client.get(f'/course/{self.course.id}/'), 'пройден')

    def test_failed_test_keeps_level_closed(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.watch(self.b)
        Attempt.objects.create(user=self.user, quiz=self.q1, correct=0, total=1, score=0, passed=False)
        self.assertEqual(self.client.get(reverse('courses:lesson', args=[self.c.id])).status_code, 302)


class CertificateTests(CourseTestBase):
    def finish_course(self):
        self.enroll_and_login()
        for lesson in (self.a, self.b):
            self.watch(lesson)
        self.pass_quiz(self.q1)
        self.watch(self.c)

    # Ф-12. Сертификат выдаётся только после всего курса
    def test_no_certificate_before_finish(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.assertFalse(Certificate.objects.exists())

    def test_certificate_after_last_test(self):
        self.finish_course()
        self.assertFalse(Certificate.objects.exists())
        self.pass_quiz(self.q2)  # сигнал courses/signals.py
        certificate = Certificate.objects.get()
        self.assertTrue(certificate.number.startswith('CP-'))

    def test_certificate_after_last_lesson(self):
        self.enroll_and_login()
        self.watch(self.a)
        self.watch(self.b)
        self.pass_quiz(self.q1)
        self.pass_quiz(self.q2)
        self.assertFalse(Certificate.objects.exists())
        data = self.watch(self.c).json()
        self.assertIsNotNone(data['certificate_url'])

    def test_one_certificate_only(self):
        self.finish_course()
        self.pass_quiz(self.q2)
        self.pass_quiz(self.q2)
        self.client.get(f'/course/{self.course.id}/')
        self.assertEqual(Certificate.objects.count(), 1)

    def test_course_page_and_my_courses_show_done(self):
        self.finish_course()
        self.pass_quiz(self.q2)
        self.assertContains(self.client.get(f'/course/{self.course.id}/'), 'Курс пройден!')
        self.assertContains(self.client.get('/my-courses/'), 'Курс пройден')

    def test_certificate_page_owner_only(self):
        self.finish_course()
        self.pass_quiz(self.q2)
        number = Certificate.objects.get().number
        url = reverse('courses:certificate', args=[number])
        self.assertContains(self.client.get(url), 'Айгерим')
        other = User.objects.create_user(username='o@test.kg', email='o@test.kg', password='x')
        self.client.force_login(other)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_check_certificate_as_guest(self):
        self.finish_course()
        self.pass_quiz(self.q2)
        number = Certificate.objects.get().number
        self.client.logout()
        url = reverse('courses:certificate_check')
        self.assertContains(self.client.get(url, {'number': number.lower()}), 'действителен')
        self.assertContains(self.client.get(url, {'number': 'CP-00000000'}), 'не найден')
