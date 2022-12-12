import shutil
import tempfile
from time import sleep
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings

from django.urls import reverse
from ..forms import PostForm
from ..models import Comment, Group, Post, Follow
from ..utils import paginator
from ..views import NUMBER_OF_POSTS, PAGE_POSTS_OF_USER
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug':
                    PostTests.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                    PostTests.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    PostTests.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    PostTests.post.pk}): 'posts/create_or_up_post.html',
            reverse('posts:post_create'): 'posts/create_or_up_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        url = reverse('posts:post_edit', kwargs={'post_id': PostTests.post.pk})
        response = self.authorized_client.get(url)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['is_edit'], True)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url = reverse('posts:post_detail', kwargs={'post_id':
                      PostTests.post.pk})
        response = self.authorized_client.get(url)
        object = response.context['post']
        self.assertEqual(object, PostTests.post)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(0, 13):
            obj = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост № {i}',
            )
            cls.posts.append(obj)
            sleep(0.01)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.posts[12].image = uploaded
        cls.posts[12].save()

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        '''
        На первой странице каталога находится планируемое число записей.
        '''
        url_and_length = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug':
                    PaginatorViewsTest.group.slug}): 10,
            reverse('posts:profile', kwargs={'username':
                    PaginatorViewsTest.user.username}): 2,
        }
        for url_rev, expected in url_and_length.items():
            with self.subTest(url_rev=url_rev):
                response = self.client.get(url_rev)
                value = len(response.context['page_obj'].object_list)
                self.assertEqual(value, expected)

    def test_last_page_contains_ten_records(self):
        '''
        На последней странице каталога находится планируемое число записей.
        '''
        url_and_length = {
            reverse('posts:index') + '?page=2': 3,
            reverse('posts:group_list', kwargs={'slug':
                    PaginatorViewsTest.group.slug}) + '?page=2': 3,
            reverse('posts:profile', kwargs={'username':
                    PaginatorViewsTest.user.username}) + '?page=7': 1,
        }
        for url_rev, expected in url_and_length.items():
            with self.subTest(url_rev=url_rev):
                response = self.client.get(url_rev)
                value = len(response.context['page_obj'].object_list)
                self.assertEqual(value, expected)

    def test_pages_contains_post_with_group(self):
        '''На страницах отображается новый созданный пост.'''
        obj = Post.objects.create(
            author=PaginatorViewsTest.user,
            group=PaginatorViewsTest.group,
            text='Тестовый пост № АААААА',
        )

        url_and_obj = {
            reverse('posts:index'): obj,
            reverse('posts:group_list', kwargs={'slug':
                    PaginatorViewsTest.group.slug}): obj,
            reverse('posts:profile', kwargs={'username':
                    PaginatorViewsTest.user.username}): obj,
        }

        for url_rev, val in url_and_obj.items():
            with self.subTest(url_rev=url_rev):
                response = self.client.get(url_rev)
                page_obj = response.context['page_obj']
                list_of_objects_on_page = page_obj.object_list
                self.assertIn(val, list_of_objects_on_page)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        url = reverse('posts:index')
        response = self.authorized_client.get(url)
        object = response.context['page_obj']
        post_list = Post.objects.select_related('author', 'group').all()
        page_obj = paginator(response.context['request'],
                             post_list, NUMBER_OF_POSTS)
        self.assertEqual(object.object_list[0].image, 'posts/small.gif')
        self.assertEqual(object.object_list, list(page_obj.object_list))
        self.assertIsInstance(object, type(page_obj))

    def test_group_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        url = reverse('posts:group_list', kwargs={'slug':
                      PaginatorViewsTest.group.slug})
        response = self.authorized_client.get(url)
        object = response.context['page_obj']
        group = Group.objects.get(slug=PaginatorViewsTest.group.slug)
        post_list = group.posts.all()
        page_obj = paginator(response.context['request'],
                             post_list, NUMBER_OF_POSTS)
        self.assertEqual(object.object_list[0].image, 'posts/small.gif')
        self.assertEqual(object.object_list, list(page_obj.object_list))
        self.assertIsInstance(object, type(page_obj))

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url = reverse('posts:profile', kwargs={'username':
                      PaginatorViewsTest.user.username})
        response = self.authorized_client.get(url)
        object = response.context['page_obj']
        user = User.objects.get(username=PaginatorViewsTest.user.username)
        post_list = user.posts.all()
        page_obj = paginator(response.context['request'],
                             post_list, PAGE_POSTS_OF_USER)
        self.assertEqual(object.object_list[0].image, 'posts/small.gif')
        self.assertEqual(object.object_list, list(page_obj.object_list))
        self.assertIsInstance(object, type(page_obj))


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_authorized_user_can_comment(self):
        '''
        Авторизированный юзер может комментировать пост.
        Проверяются: статус код, страница перенаправления,
        изменение кол-ва комментов.
        '''
        comments_count_1 = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария'
        }
        url = reverse('posts:add_comment',
                      kwargs={'post_id': CommentTest.post.pk})
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        comments_count_2 = Comment.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': CommentTest.post.pk}))
        self.assertEqual(comments_count_1 + 1, comments_count_2)

    def test_guest_user_NOT_can_comment(self):
        '''
        НЕавторизированный юзер НЕ может комментировать пост.
        Проверяются: статус код, страница перенаправления,
        изменение кол-ва комментов.
        '''
        comments_count_1 = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария'
        }
        url = reverse('posts:add_comment',
                      kwargs={'post_id': CommentTest.post.pk})
        response = self.guest_client.post(
            url,
            data=form_data,
            follow=True
        )
        comments_count_2 = Comment.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('users:login') + '?next=' + url)
        self.assertEqual(comments_count_1, comments_count_2)

    def test_page_contains_new_comment(self):
        '''
        Новый комментарий отображается на странице.
        '''
        form_data = {
            'text': 'Тестовый текст комментария'
        }
        url = reverse('posts:add_comment',
                      kwargs={'post_id': CommentTest.post.pk})
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.get(pk=1),
                         response.context['comments'][0])


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create(username='user1')
        cls.user2 = User.objects.create(username='user2')
        cls.user3 = User.objects.create(username='user3')
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )

    def setUp(self):
        super().setUp()
        self.user1_client = Client()
        self.user1_client.force_login(FollowingTest.user1)

    def test_authorized_client_can_follow(self):
        '''
        Авторизированный пользователь может подписаться на других
        пользователей.
        '''
        url = reverse('posts:profile_follow',
                      kwargs={'username': FollowingTest.user3.username})
        self.user1_client.get(url)
        self.assertTrue(
            Follow.objects.filter(
                user=FollowingTest.user1,
                author=FollowingTest.user3,
            ).exists()
        )

    def test_authorized_client_can_delete_follow(self):
        '''
        Авторизированный пользователь может удалять пользователей из
        своих подписок.
        '''
        url = reverse('posts:profile_unfollow',
                      kwargs={'username': FollowingTest.user2.username})
        self.user1_client.get(url)
        self.assertFalse(
            Follow.objects.filter(
                user=FollowingTest.user1,
                author=FollowingTest.user2,
            ).exists()
        )

    def test_new_post_in_page_for_followers_and_not_followers(self):
        '''
        Новый пост есть на странице подписчика автора поста.
        Новый пост отсутствует на странице НЕподписчика автора поста.
        '''
        Post.objects.create(text='Текст user2', author=FollowingTest.user2)
        Post.objects.create(text='Текст user3', author=FollowingTest.user3)
        url = reverse('posts:follow_index')
        response = self.user1_client.get(url)
        self.assertIn(Post.objects.get(pk=1),
                      response.context['page_obj'].object_list)
        self.assertNotIn(Post.objects.get(pk=2),
                         response.context['page_obj'].object_list)
