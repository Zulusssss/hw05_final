from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.contrib.auth.tokens import default_token_generator

from django.urls import reverse

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('user')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_user(self):
        'Проверка регистрации пользователя.'
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Первое имя',
            'last_name': 'Последнее имя',
            'username': 'auth',
            'email': 'auth@gmai.com',
            'password1': 'barakuda12345678',
            'password2': 'barakuda12345678',

        }
        response = PostFormTests.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        url = reverse('posts:index')
        self.assertRedirects(response, url)
        self.assertEqual(User.objects.count(), users_count + 1)

        self.assertTrue(
            User.objects.filter(
                first_name='Первое имя',
                last_name='Последнее имя',
                username='auth',
                email='auth@gmai.com',
            ).exists()
        )

    def test_password_reset_confirm_creation_of_page(self):
        '''
        Проверка создания страницы с назначением нового пароля по ссылке из
        письма со сменой пароля по email для пользователя.
        '''
        uid = urlsafe_base64_encode(force_bytes(PostFormTests.user.pk))
        token = default_token_generator.make_token(PostFormTests.user)
        url = reverse('users:password_reset_confirm',
                      kwargs={'uidb64': uid, 'token': token})
        response = PostFormTests.authorized_client.get(url)
        response = PostFormTests.authorized_client.get(response.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/password_reset_confirm.html')
