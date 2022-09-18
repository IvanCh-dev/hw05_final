from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus
from ..models import Group, Post


User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.UNAUTHORIZED_URLS = {
            HTTPStatus.OK: {
                '/': 'posts/index.html',
                '/group/test-slug-1/': 'posts/group_list.html',
                '/profile/test_user/': 'posts/profile.html',
                '/posts/1/': 'posts/post_detail.html',
            },
            HTTPStatus.FOUND: {
                '/create/': 'users/login.html',
                '/posts/1/edit/': 'users/login.html',
            },
            HTTPStatus.NOT_FOUND: {
                '/unexisting_page/': 'core/404.html',
            }
        }

        cls.AUTHORIZED_NO_AUTHOR_URLS = {
            HTTPStatus.OK: {
                '/': 'posts/index.html',
                '/group/test-slug-1/': 'posts/group_list.html',
                '/profile/test_user/': 'posts/profile.html',
                '/posts/1/': 'posts/post_detail.html',
                '/create/': 'posts/create_post.html',
            },
            HTTPStatus.FOUND: {
                '/posts/1/edit/': 'posts/post_detail.html',
            },
        }

        cls.AUTHORIZED_AUTHOR_URLS = {
            HTTPStatus.OK: {
                '/': 'posts/index.html',
                '/group/test-slug-1/': 'posts/group_list.html',
                '/profile/test_user/': 'posts/profile.html',
                '/posts/1/': 'posts/post_detail.html',
                '/create/': 'posts/create_post.html',
                '/posts/1/edit/': 'posts/create_post.html',
            },
        }
        cls.auth = User.objects.create_user(username='auth')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа номер 1',
            slug='test-slug-1',
            description='Тестовое описание номер 1',
        )
        cls.post_1 = Post.objects.create(
            id=1,
            author=cls.auth,
            text='Тестовый пост номер 1',
        )
        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.auth)
        cls.test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.test_user)

    def test_unauthorized_user(self):
        """Проверка ответа сервера для неавторизованного пользователя."""
        for status, urls in self.UNAUTHORIZED_URLS.items():
            if status == HTTPStatus.FOUND:
                for url, template in urls.items():
                    response = self.guest_client.get(url, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)
            else:
                for url, template in urls.items():
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, status)
                    self.assertTemplateUsed(response, template)

    def test_authorized_no_author(self):
        """Проверка ответа сервера для авторизованного не автора."""
        for status, urls in self.AUTHORIZED_NO_AUTHOR_URLS.items():
            if status == HTTPStatus.FOUND:
                for url, template in urls.items():
                    response = self.authorized_test_user.get(url, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)
            else:
                for url, template in urls.items():
                    response = self.authorized_test_user.get(url)
                    self.assertEqual(response.status_code, status)
                    self.assertTemplateUsed(response, template)

    def test_authorized_author(self):
        """Проверка ответа сервера для авторизованного автора."""
        for status, urls in self.AUTHORIZED_AUTHOR_URLS.items():
            if status == HTTPStatus.FOUND:
                for url, template in urls.items():
                    response = self.authorized_auth.get(url, follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)
            else:
                for url, template in urls.items():
                    response = self.authorized_auth.get(url)
                    self.assertEqual(response.status_code, status)
                    self.assertTemplateUsed(response, template)

    def test_add_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        url = '/posts/1/comment/'
        template_login = 'users/login.html'
        response = self.guest_client.get(url, follow=True)
        self.assertTemplateUsed(response, template_login)
