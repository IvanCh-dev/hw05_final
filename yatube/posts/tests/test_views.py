from django.forms import fields
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from .. models import Follow, Group, Post
from .. forms import PostForm
from .. views import DISPLAYED_POSTS


User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded_image = SimpleUploadedFile(
            'small.gif', small_gif, content_type='image/gif')
        cls.user_auth = User.objects.create_user(username='auth')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа номер 1',
            slug='test-slug-1',
            description='Тестовое описание номер 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа номер 2',
            slug='test-slug-2',
            description='Тестовое описание номер 2',
        )
        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.user_auth)
        cls.user_test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.user_test_user)
        cls.user_test_user_2 = User.objects.create_user(username='test_user_2')
        cls.authorized_test_user_2 = Client()
        cls.authorized_test_user_2.force_login(cls.user_test_user_2)
        cls.posts_list = []
        for i in range(1, 16):
            cls.posts_list.append(
                Post(
                    id=i,
                    author=cls.user_auth,
                    text=f'Пост {i}',
                    group=cls.group_1,
                )
            )
        Post.objects.bulk_create(cls.posts_list)
        cls.posts_list.append(
            Post.objects.create(
                id=16,
                author=cls.user_test_user,
                text='Пост 16',
                group=cls.group_2,
                image=uploaded_image,
            )
        )

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group_1.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.user_auth.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.posts_list[15].id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.posts_list[0].id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        for i in range(3):
            firsts_object = response.context['page_obj'][i]
            self.assertEqual(
                firsts_object.text, self.posts_list[-1 - i].text)
        first_object = response.context['page_obj'][0]
        self.assertEqual(
            first_object.image, self.posts_list[15].image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        group_1 = response.context['group']
        self.assertEqual(group_1.title, self.group_1.title)
        self.assertEqual(group_1.slug, self.group_1.slug)
        self.assertEqual(group_1.description, self.group_1.description)
        for i in range(3):
            first_object = response.context['page_obj'][i]
            self.assertEqual(
                first_object.text, self.posts_list[-2 - i].text)
            self.assertEqual(first_object.author, self.user_auth)
            self.assertEqual(first_object.group, self.group_1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_auth.username}
            )
        )
        user = response.context['author']
        self.assertEqual(user, self.user_auth)
        for i in range(3):
            first_object = response.context['page_obj'][i]
            self.assertEqual(
                first_object.text, self.posts_list[-2 - i].text)
            self.assertEqual(first_object.author, self.user_auth)
            self.assertEqual(first_object.group, self.group_1)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 16})
        )
        post = response.context['post']
        self.assertEqual(post.id, 16)
        self.assertEqual(post.text, 'Пост 16')
        self.assertEqual(post.author.username, 'test_user')
        self.assertEqual(post.group, self.group_2)
        self.assertEqual(post.image, self.posts_list[15].image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_test_user.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': fields.CharField,
            'group': fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context.get('form')
                self.assertIsNotNone(form)
                self.assertIsInstance(form, PostForm)
                self.assertIsInstance(form.fields.get(field_name), field_type)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_test_user.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.posts_list[-1].id}
            )
        )
        form_fields = {
            'text': fields.CharField,
            'group': fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context.get('form')
                self.assertIsNotNone(form)
                self.assertIsInstance(form, PostForm)
                self.assertIsInstance(form.fields.get(field_name), field_type)

    def test_paginator(self):
        """Paginator index, group_list, profile"""
        urls_to_check = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}),
            reverse('posts:profile', kwargs={
                'username': self.user_auth.username}
            ),
        ]
        latest_posts = Post.objects.filter(
            author__username=self.user_auth.username).all()[:DISPLAYED_POSTS]
        for url in urls_to_check:
            response = self.guest_client.get(url)
            context = response.context
            with self.subTest(url=url):
                if url == reverse('posts:index'):
                    latest_posts = Post.objects.all()[:DISPLAYED_POSTS]
                page_obj = context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    latest_posts, page_obj, transform=lambda x: x)
                if url == reverse('posts:index'):
                    latest_posts = Post.objects.filter(
                        author__username=(
                            self.user_auth.username)).all()[:DISPLAYED_POSTS]

    def test_create_post_correct_group_and_profile(self):
        """
        Отображение поста в group_list и profile после его создания.
        """
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug})
        )
        post_other_user_group = response.context['page_obj'][0]
        self.assertEqual(post_other_user_group.text, self.posts_list[-1].text)
        self.assertEqual(
            post_other_user_group.image, self.posts_list[15].image)
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_test_user.username}
            )
        )
        post_16 = response.context['page_obj'][0]
        self.assertEqual(post_16.text, self.posts_list[-1].text)
        self.assertEqual(post_16.image, self.posts_list[15].image)

    def test_cache_index(self):
        """Кэш на главной странице работает исправно."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        Post.objects.get(id=16).delete()
        self.assertEqual(
            first_object.text, self.posts_list[15].text)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(
            first_object.text, self.posts_list[14].text)

    def test_subscribtions(self):
        """Подписки работают исправно."""
        self.authorized_test_user_2.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_test_user.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user_test_user_2.id).exists())
        response = self.authorized_test_user_2.get(
            reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 1)
        response = self.authorized_auth.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 0)
        self.authorized_test_user_2.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user_test_user.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user_test_user_2.id).exists())
