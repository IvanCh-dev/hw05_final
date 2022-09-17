from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        self.assertEqual(
            group.__str__(),
            group.title,
            'Test __str__ group model failed'
        )
        self.assertEqual(
            post.__str__(),
            post.text[:15],
            'Test __str__ post model failed'
        )

    def test_verbose_name(self):
        """
        Проверяем, что у моделей корректно работают verbose_name.
        """
        post = PostModelTest.post
        dct_verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Название группы',
        }
        for field, value in dct_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, value)

    def test_help_text(self):
        """
        Проверяем, что у моделей корректно работают help_text.
        """
        post = PostModelTest.post
        dct_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, value in dct_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, value)
