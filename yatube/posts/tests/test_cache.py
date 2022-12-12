from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from django.urls import reverse
from ..models import Group, Post

from django.core.cache import cache

User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.post = Post.objects.create(
            author=CacheTest.user,
            text='Тестовый пост',
        )

    def test_deleted_post_save_in_cache(self):
        '''
        Пост сохраняется в кэше после удаления самого поста из БД.
        '''
        response_1 = self.guest_client.get(reverse('posts:index'))
        Post.objects.get(pk=1).delete()
        response_2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)
