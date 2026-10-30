# Ответственная: Нургуль (Ф-1, Ф-2, Ф-3, Ф-13)
# Автотесты входа, выдачи аккаунта, восстановления пароля и профиля.
# Запуск: python manage.py test accounts
import re
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@test.kg', username='admin', password='Admin12345!')
        self.user = User.objects.create_user(
            username='u@test.kg', email='u@test.kg', first_name='Айгерим', password='Pass12345!')

    # Ф-1. Самостоятельной регистрации нет
    def test_no_registration_page(self):
        self.assertEqual(self.client.get('/accounts/register/').status_code, 404)
        self.assertNotContains(self.client.get('/'), 'Регистрация')

    # Ф-1. Админ создаёт аккаунт — логин и пароль уходят на почту
    def test_admin_creates_account_and_mail_sent(self):
        self.client.force_login(self.admin)
        response = self.client.post('/admin/accounts/user/add/',
                                    {'email': 'new@test.kg', 'first_name': 'Нова', '_save': '1'}, follow=True)
        self.assertContains(response, 'Логин и пароль отправлены на new@test.kg')
        self.assertEqual(len(mail.outbox), 1)
        password = re.search(r'Пароль: (\S+)', mail.outbox[0].body).group(1)
        user = User.objects.get(email='new@test.kg')
        self.assertNotIn(password, user.password)  # в базе только хеш (п. 4.2 ТЗ)
        self.assertTrue(self.client.login(username='new@test.kg', password=password))

    def test_duplicate_email_rejected(self):
        self.client.force_login(self.admin)
        self.client.post('/admin/accounts/user/add/', {'email': 'u@test.kg', 'first_name': 'X', '_save': '1'})
        self.assertEqual(User.objects.filter(email='u@test.kg').count(), 1)

    def test_mail_failure_shows_password_to_admin(self):
        self.client.force_login(self.admin)
        with mock.patch('accounts.emails.send_mail', side_effect=OSError):
            response = self.client.post('/admin/accounts/user/add/',
                                        {'email': 'f@test.kg', 'first_name': 'Ф', '_save': '1'}, follow=True)
        self.assertContains(response, 'письмо не отправилось')

    # Ф-2. Вход: ученик — в «Мои курсы», админ — в панель
    def test_student_login_redirect(self):
        response = self.client.post(reverse('login'), {'username': 'u@test.kg', 'password': 'Pass12345!'})
        self.assertRedirects(response, reverse('courses:my_courses'))

    def test_admin_login_redirect(self):
        response = self.client.post(reverse('login'), {'username': 'admin@test.kg', 'password': 'Admin12345!'})
        self.assertEqual(response['Location'], '/admin/')

    def test_wrong_password(self):
        response = self.client.post(reverse('login'), {'username': 'u@test.kg', 'password': 'wrong'})
        self.assertContains(response, 'Неверная почта или пароль')

    def test_logout(self):
        self.client.force_login(self.user)
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('profile')).status_code, 302)

    # Ф-3. Восстановление пароля по ссылке из письма
    def test_password_reset_flow(self):
        self.client.post(reverse('password_reset'), {'email': 'u@test.kg'})
        link = re.search(r'http://testserver(/accounts/reset/\S+/)', mail.outbox[0].body).group(1)
        response = self.client.get(link, follow=True)
        url = response.redirect_chain[-1][0]
        self.client.post(url, {'new_password1': 'NewPass789!x', 'new_password2': 'NewPass789!x'})
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password('NewPass789!x'))
        self.assertIn('пароль изменён', mail.outbox[-1].subject)

    def test_reset_unknown_email_does_not_tell(self):
        # Не выдаём, есть ли такая почта в базе: страница одна и та же
        response = self.client.post(reverse('password_reset'), {'email': 'nobody@test.kg'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    # Ф-13. Профиль
    def test_profile_needs_login(self):
        self.assertEqual(self.client.get(reverse('profile')).status_code, 302)

    def test_generated_avatar_shown(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('profile')), '<svg')

    def test_empty_name_rejected(self):
        self.client.force_login(self.user)
        self.client.post(reverse('profile'), {'first_name': ''})
        self.assertEqual(User.objects.get(pk=self.user.pk).first_name, 'Айгерим')

    def test_password_change_and_mail(self):
        self.client.force_login(self.user)
        self.client.post(reverse('password_change'), {
            'old_password': 'Pass12345!', 'new_password1': 'Other456!q', 'new_password2': 'Other456!q'})
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password('Other456!q'))
        self.assertEqual(len(mail.outbox), 1)

    def test_password_change_wrong_old(self):
        self.client.force_login(self.user)
        self.client.post(reverse('password_change'), {
            'old_password': 'bad', 'new_password1': 'Other456!q', 'new_password2': 'Other456!q'})
        self.assertTrue(User.objects.get(pk=self.user.pk).check_password('Pass12345!'))
        self.assertEqual(len(mail.outbox), 0)
