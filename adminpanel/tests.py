# Ответственная: Фатима (А-1 – А-6) — этап Э5
# Автотесты панели администратора. Запуск: python manage.py test adminpanel
import re
from unittest import mock

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Enrollment, Lesson, LessonProgress, Level, Material
from quizzes.models import Answer, Attempt, Question, Quiz


class PanelTestBase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email='admin@test.kg', username='admin', password='Admin123!')
        self.student = User.objects.create_user(username='s@test.kg', email='s@test.kg',
                                                first_name='Айгерим', password='Pass12345!')
        self.course = Course.objects.create(title='Python', is_published=True)
        self.level = Level.objects.create(course=self.course, title='Старт', order=1)
        self.lesson = Lesson.objects.create(level=self.level, title='Урок 1', order=1)
        self.client.force_login(self.admin)


class AccessTests(PanelTestBase):
    # Только администратор (п. 4.2 ТЗ: функции администратора недоступны пользователю)
    def test_guest_goes_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_student_has_no_access(self):
        self.client.force_login(self.student)
        for name in ('dashboard', 'course_list', 'user_list', 'progress'):
            self.assertRedirects(self.client.get(reverse(f'adminpanel:{name}')), '/', fetch_redirect_response=False)

    def test_student_cannot_post(self):
        self.client.force_login(self.student)
        self.client.post(reverse('adminpanel:course_toggle', args=[self.course.pk]))
        self.assertTrue(Course.objects.get(pk=self.course.pk).is_published)

    def test_all_pages_open_for_admin(self):
        quiz = Quiz.objects.create(level=self.level, title='Тест')
        urls = [reverse('adminpanel:dashboard'), reverse('adminpanel:course_list'),
                reverse('adminpanel:course_create'), reverse('adminpanel:course_detail', args=[self.course.pk]),
                reverse('adminpanel:level_create', args=[self.course.pk]),
                reverse('adminpanel:lesson_edit', args=[self.lesson.pk]),
                reverse('adminpanel:quiz_edit', args=[self.level.pk]),
                reverse('adminpanel:question_create', args=[self.level.pk]),
                reverse('adminpanel:user_list'), reverse('adminpanel:user_create'),
                reverse('adminpanel:user_progress', args=[self.student.pk]), reverse('adminpanel:progress')]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertTrue(quiz)

    # п. 4.1.4: после входа админ — в панель; каталога и «Моих курсов» у него нет
    def test_admin_login_goes_to_panel(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'admin@test.kg', 'password': 'Admin123!'})
        self.assertEqual(response['Location'], reverse('adminpanel:dashboard'))

    def test_admin_has_no_catalog_and_my_courses(self):
        self.assertRedirects(self.client.get('/'), reverse('adminpanel:dashboard'))
        self.assertRedirects(self.client.get(reverse('courses:my_courses')), reverse('adminpanel:dashboard'))

    def test_student_menu_has_no_panel(self):
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get('/'), 'Панель администратора')


class CourseTests(PanelTestBase):
    # А-1. Курсы
    def test_create_course(self):
        response = self.client.post(reverse('adminpanel:course_create'),
                                    {'title': 'Django', 'description': 'Сайты', 'is_published': ''})
        course = Course.objects.get(title='Django')
        self.assertFalse(course.is_published)
        self.assertRedirects(response, reverse('adminpanel:course_detail', args=[course.pk]))

    def test_empty_title_rejected(self):
        response = self.client.post(reverse('adminpanel:course_create'), {'title': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.count(), 1)

    def test_edit_course(self):
        self.client.post(reverse('adminpanel:course_edit', args=[self.course.pk]),
                         {'title': 'Python 2', 'description': '', 'is_published': 'on'})
        self.assertEqual(Course.objects.get(pk=self.course.pk).title, 'Python 2')

    def test_hide_and_publish(self):
        url = reverse('adminpanel:course_toggle', args=[self.course.pk])
        self.client.post(url)
        self.assertFalse(Course.objects.get(pk=self.course.pk).is_published)
        self.client.logout()
        self.assertNotContains(self.client.get('/'), 'Python')  # скрытого нет в каталоге
        self.client.force_login(self.admin)
        self.client.post(url)
        self.assertTrue(Course.objects.get(pk=self.course.pk).is_published)

    def test_toggle_needs_post(self):
        self.assertEqual(self.client.get(reverse('adminpanel:course_toggle', args=[self.course.pk])).status_code, 405)

    def test_next_to_other_site_ignored(self):
        response = self.client.post(reverse('adminpanel:course_toggle', args=[self.course.pk]),
                                    {'next': 'https://evil.example.com/'})
        self.assertEqual(response['Location'], reverse('adminpanel:course_list'))

    def test_delete_course(self):
        self.client.post(reverse('adminpanel:course_delete', args=[self.course.pk]))
        self.assertFalse(Course.objects.exists())
        self.assertFalse(Lesson.objects.exists())


class LevelLessonTests(PanelTestBase):
    # А-2. Уровни
    def test_add_level_with_next_number(self):
        self.assertContains(self.client.get(reverse('adminpanel:level_create', args=[self.course.pk])), 'value="2"')
        self.client.post(reverse('adminpanel:level_create', args=[self.course.pk]), {'title': 'Циклы', 'order': 2})
        self.assertEqual(self.course.levels.count(), 2)

    def test_duplicate_level_number_rejected(self):
        response = self.client.post(reverse('adminpanel:level_create', args=[self.course.pk]),
                                    {'title': 'Дубль', 'order': 1})
        self.assertContains(response, 'уже есть')
        self.assertEqual(self.course.levels.count(), 1)

    def test_delete_level(self):
        self.client.post(reverse('adminpanel:level_delete', args=[self.level.pk]))
        self.assertFalse(Level.objects.exists())

    # А-3. Уроки: видео файлом или ссылкой, материалы
    def test_lesson_with_video_file(self):
        self.client.post(reverse('adminpanel:lesson_create', args=[self.level.pk]), {
            'title': 'Урок 2', 'order': 2, 'description': 'Текст',
            'video': SimpleUploadedFile('v.mp4', b'0', 'video/mp4'), 'video_url': ''})
        self.assertTrue(Lesson.objects.get(title='Урок 2').video)

    def test_lesson_wrong_video_type(self):
        response = self.client.post(reverse('adminpanel:lesson_create', args=[self.level.pk]), {
            'title': 'Урок 2', 'order': 2, 'video': SimpleUploadedFile('v.exe', b'0'), 'video_url': ''})
        self.assertContains(response, 'Загрузите видео')
        self.assertFalse(Lesson.objects.filter(title='Урок 2').exists())

    def test_lesson_with_youtube_link(self):
        self.client.post(reverse('adminpanel:lesson_edit', args=[self.lesson.pk]), {
            'title': 'Урок 1', 'order': 1, 'video_url': 'https://youtu.be/dQw4w9WgXcQ'})
        lesson = Lesson.objects.get(pk=self.lesson.pk)
        self.assertEqual(lesson.youtube_embed, 'https://www.youtube.com/embed/dQw4w9WgXcQ')
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.force_login(self.student)
        html = self.client.get(reverse('courses:lesson', args=[lesson.pk])).content.decode()
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', html)
        self.assertIn('Отметить урок как изученный', html)  # 90 % у YouTube не посчитать

    def test_bad_link_rejected(self):
        response = self.client.post(reverse('adminpanel:lesson_edit', args=[self.lesson.pk]), {
            'title': 'Урок 1', 'order': 1, 'video_url': 'не ссылка'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lesson.objects.get(pk=self.lesson.pk).video_url, '')

    def test_add_and_delete_material(self):
        url = reverse('adminpanel:material_add', args=[self.lesson.pk])
        self.client.post(url, {'title': 'Конспект', 'file': SimpleUploadedFile('a.pdf', b'%PDF', 'application/pdf')})
        material = Material.objects.get()
        self.client.post(url, {'title': 'Вирус', 'file': SimpleUploadedFile('a.exe', b'MZ')})
        self.assertEqual(Material.objects.count(), 1)  # .exe не принят
        self.client.post(reverse('adminpanel:material_delete', args=[material.pk]))
        self.assertFalse(Material.objects.exists())


class QuizBuilderTests(PanelTestBase):
    # А-4. Конструктор тестов
    def test_create_quiz_with_threshold(self):
        self.client.post(reverse('adminpanel:quiz_edit', args=[self.level.pk]), {'title': 'Тест', 'pass_score': 70})
        self.assertEqual(Quiz.objects.get(level=self.level).pass_score, 70)

    def test_threshold_over_100_rejected(self):
        self.client.post(reverse('adminpanel:quiz_edit', args=[self.level.pk]), {'title': 'Тест', 'pass_score': 150})
        self.assertFalse(Quiz.objects.exists())

    def test_question_needs_quiz_first(self):
        response = self.client.get(reverse('adminpanel:question_create', args=[self.level.pk]))
        self.assertRedirects(response, reverse('adminpanel:quiz_edit', args=[self.level.pk]))

    def test_add_question_with_correct_answer(self):
        quiz = Quiz.objects.create(level=self.level, title='Тест')
        self.client.post(reverse('adminpanel:question_create', args=[self.level.pk]), {
            'text': '2+2?', 'answer_1': '3', 'answer_2': '4', 'answer_3': '', 'answer_4': '', 'correct': '2'})
        question = quiz.questions.get()
        self.assertEqual([(a.text, a.is_correct) for a in question.answers.order_by('id')], [('3', False), ('4', True)])

    def test_correct_cannot_be_empty(self):
        Quiz.objects.create(level=self.level, title='Тест')
        response = self.client.post(reverse('adminpanel:question_create', args=[self.level.pk]), {
            'text': '?', 'answer_1': 'a', 'answer_2': 'b', 'answer_3': '', 'answer_4': '', 'correct': '3'})
        self.assertContains(response, 'не может быть пустым')
        self.assertFalse(Question.objects.exists())

    def test_edit_and_delete_question(self):
        quiz = Quiz.objects.create(level=self.level, title='Тест')
        question = Question.objects.create(quiz=quiz, text='Старый')
        Answer.objects.create(question=question, text='a', is_correct=True)
        Answer.objects.create(question=question, text='b')
        url = reverse('adminpanel:question_edit', args=[self.level.pk, question.pk])
        self.assertContains(self.client.get(url), 'Старый')
        self.client.post(url, {'text': 'Новый', 'answer_1': 'x', 'answer_2': 'y', 'answer_3': 'z', 'answer_4': '', 'correct': '3'})
        question.refresh_from_db()
        self.assertEqual(question.text, 'Новый')
        self.assertEqual(question.answers.get(is_correct=True).text, 'z')
        self.client.post(reverse('adminpanel:question_delete', args=[question.pk]))
        self.assertFalse(Question.objects.exists())


class UserTests(PanelTestBase):
    # А-5. Пользователи
    def test_create_user_sends_login_and_password(self):
        self.client.post(reverse('adminpanel:user_create'), {'email': 'new@test.kg', 'first_name': 'Нова'})
        password = re.search(r'Пароль: (\S+)', mail.outbox[0].body).group(1)
        self.assertTrue(self.client.login(username='new@test.kg', password=password))

    def test_create_user_mail_failure_shows_password(self):
        with mock.patch('accounts.emails.send_mail', side_effect=OSError):
            response = self.client.post(reverse('adminpanel:user_create'),
                                        {'email': 'f@test.kg', 'first_name': 'Ф'}, follow=True)
        self.assertContains(response, 'письмо не отправилось')

    def test_duplicate_email_rejected(self):
        self.client.post(reverse('adminpanel:user_create'), {'email': 's@test.kg', 'first_name': 'X'})
        self.assertEqual(User.objects.filter(email='s@test.kg').count(), 1)

    def test_list_and_search(self):
        User.objects.create_superuser(email='boss@test.kg', username='boss', password='x')
        response = self.client.get(reverse('adminpanel:user_list'), {'q': 'айгер'})
        self.assertContains(response, 's@test.kg')  # поиск по имени кириллицей, без учёта регистра
        response = self.client.get(reverse('adminpanel:user_list'))
        self.assertNotContains(response, 'boss@test.kg')  # админы в списке учеников не показываются

    def test_block_and_unblock(self):
        url = reverse('adminpanel:user_toggle', args=[self.student.pk])
        self.client.post(url)
        self.assertFalse(User.objects.get(pk=self.student.pk).is_active)
        self.assertFalse(self.client.login(username='s@test.kg', password='Pass12345!'))  # войти нельзя
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('adminpanel:user_list'), {'status': 'blocked'}), 's@test.kg')
        self.client.post(url)
        self.assertTrue(self.client.login(username='s@test.kg', password='Pass12345!'))

    def test_admin_cannot_be_blocked_here(self):
        response = self.client.post(reverse('adminpanel:user_toggle', args=[self.admin.pk]))
        self.assertEqual(response.status_code, 404)

    def test_new_password(self):
        self.client.post(reverse('adminpanel:user_new_password', args=[self.student.pk]))
        password = re.search(r'Пароль: (\S+)', mail.outbox[0].body).group(1)
        self.assertIn('новый пароль', mail.outbox[0].subject)
        self.assertFalse(self.client.login(username='s@test.kg', password='Pass12345!'))  # старый не работает
        self.assertTrue(self.client.login(username='s@test.kg', password=password))


class ProgressTests(PanelTestBase):
    # А-6. Прогресс любого пользователя
    def test_user_progress(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        LessonProgress.objects.create(user=self.student, lesson=self.lesson)
        response = self.client.get(reverse('adminpanel:user_progress', args=[self.student.pk]))
        self.assertContains(response, 'Python')
        self.assertContains(response, '100 %')
        self.assertContains(response, '1 из 1')

    def test_overview_filter_by_course(self):
        other = Course.objects.create(title='Django', is_published=True)
        Enrollment.objects.create(user=self.student, course=self.course)
        Enrollment.objects.create(user=self.student, course=other)
        response = self.client.get(reverse('adminpanel:progress'), {'course': other.pk})
        self.assertContains(response, '<td>Django</td>', html=False)
        self.assertNotContains(response, '<td>Python</td>', html=False)

    def test_dashboard_numbers(self):
        quiz = Quiz.objects.create(level=self.level, title='Тест')
        Attempt.objects.create(user=self.student, quiz=quiz, correct=1, total=1, score=100, passed=True)
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertContains(response, 'попыток тестов')
        self.assertContains(response, 's@test.kg')


class EnrollmentByAdminTests(PanelTestBase):
    # Сверх ТЗ: администратор записывает ученика на курс и отчисляет
    def test_admin_enrolls_student(self):
        response = self.client.post(reverse('adminpanel:enrollment_add'),
                                    {'user': self.student.pk, 'course': self.course.pk}, follow=True)
        self.assertTrue(Enrollment.objects.filter(user=self.student, course=self.course).exists())
        self.assertContains(response, 'записан на курс')
        # курс появился у ученика в «Моих курсах»
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('courses:my_courses')), 'Python')

    def test_second_enroll_no_duplicate(self):
        for _ in range(2):
            self.client.post(reverse('adminpanel:enrollment_add'), {'user': self.student.pk, 'course': self.course.pk})
        self.assertEqual(Enrollment.objects.filter(user=self.student, course=self.course).count(), 1)

    def test_hidden_course_admin_and_bad_input_refused(self):
        hidden = Course.objects.create(title='Черновик')
        url = reverse('adminpanel:enrollment_add')
        self.assertEqual(self.client.post(url, {'user': self.student.pk, 'course': hidden.pk}).status_code, 404)
        self.assertEqual(self.client.post(url, {'user': self.admin.pk, 'course': self.course.pk}).status_code, 404)
        self.assertEqual(self.client.post(url, {'user': 'abc', 'course': ''}).status_code, 404)
        self.assertEqual(self.client.get(url).status_code, 405)  # только POST
        self.assertFalse(Enrollment.objects.exists())

    def test_admin_removes_enrollment(self):
        enrollment = Enrollment.objects.create(user=self.student, course=self.course)
        self.client.post(reverse('adminpanel:enrollment_remove', args=[enrollment.pk]))
        self.assertFalse(Enrollment.objects.filter(pk=enrollment.pk).exists())

    def test_student_cannot_enroll_others(self):
        other = User.objects.create_user(username='o@test.kg', email='o@test.kg', password='Pass12345!')
        enrollment = Enrollment.objects.create(user=other, course=self.course)
        self.client.force_login(self.student)
        self.client.post(reverse('adminpanel:enrollment_add'), {'user': other.pk, 'course': self.course.pk})
        self.client.post(reverse('adminpanel:enrollment_remove', args=[enrollment.pk]))
        self.assertTrue(Enrollment.objects.filter(pk=enrollment.pk).exists())

    def test_pages_show_new_controls(self):
        self.assertContains(self.client.get(reverse('adminpanel:progress')), 'Записать ученика на курс')
        self.assertContains(self.client.get(reverse('adminpanel:user_progress', args=[self.student.pk])), 'Записать на курс')
        self.assertContains(self.client.get(reverse('adminpanel:dashboard')), 'Быстрые действия')
        self.assertContains(self.client.get(reverse('adminpanel:course_detail', args=[self.course.pk])), '+ Тест уровня')


CONSOLE_MAIL = {'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'}}


class MailNotConfiguredTests(PanelTestBase):
    # Нет файла .env — панель предупреждает и показывает пароль на экране
    def test_dashboard_warns(self):
        from django.test import override_settings
        with override_settings(MAILERS=CONSOLE_MAIL):
            self.assertContains(self.client.get(reverse('adminpanel:dashboard')), 'Почта не настроена')
        self.assertNotContains(self.client.get(reverse('adminpanel:dashboard')), 'Почта не настроена')

    def test_create_user_shows_password(self):
        from django.test import override_settings
        with override_settings(MAILERS=CONSOLE_MAIL), mock.patch('sys.stdout'):
            response = self.client.post(reverse('adminpanel:user_create'),
                                        {'email': 'new@test.kg', 'first_name': 'Азамат'}, follow=True)
        self.assertContains(response, 'почта не настроена')
        self.assertContains(response, 'пароль ')
        self.assertTrue(User.objects.filter(email='new@test.kg').exists())
