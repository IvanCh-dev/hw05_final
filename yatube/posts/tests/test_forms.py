from .. forms import PostForm
from .. models import Post, Group, Comment
import os
import shutil
import tempfile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FileField, ImageFieldFile


User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user_test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.user_test_user)
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
        Post.objects.create(
            id=1,
            text='Тестовый пост номер 1',
            author=cls.user_test_user,
        )
        Post.objects.create(
            id=2,
            text='Тестовый пост номер 2',
            author=cls.user_test_user,
        )
        cls.form = PostForm()

    def setUp(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded_image = SimpleUploadedFile(
            'small.gif', small_gif, content_type='image/gif')

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_create_form(self):
        """Форма post_create работает правильно при создании поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост номер 3',
            'group': self.group_1.id,
            'image': self.uploaded_image,
        }
        response = self.authorized_test_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'test_user'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_3 = Post.objects.get(text='Тестовый пост номер 3')
        self.assertEqual(
            User.objects.get(username='test_user').username,
            post_3.author.username
        )
        self.assertEqual(
            Group.objects.get(title='Тестовая группа номер 1').title,
            post_3.group.title
        )
        # self.assertEqual(post_3.image,
        #                  self.uploaded_image)
        image = ImageFieldFile(
            name='posts/small.gif',
            instance=post_3,
            field=FileField(),
        )
        self.assertEqual(post_3.image, image)

    def test_edit_form(self):
        """Форма post_create работает правильно при редактировании поста"""
        form_data = {
            'text': 'Тестовый пост номер 2 c изменениями',
            'group': self.group_2.id,
            'image': self.uploaded_image,
        }
        response = self.authorized_test_user.post(
            reverse('posts:post_edit', kwargs={'post_id': 2}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=2)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': 2}))
        self.assertEqual(
            post_2.text,
            'Тестовый пост номер 2 c изменениями'
        )
        self.assertFalse(
            post_2.group.title
            == 'Тестовая группа номер 1'
        )
        self.assertEqual(os.path.basename(post_2.image.name),
                         self.uploaded_image.name)
        self.assertEqual(list(post_2.image.chunks()),
                         list(self.uploaded_image.chunks()))

    def test_comments(self):
        """Комментарий появляется на странице поста."""
        form_data = {
            'text': 'Тестовый комментарий 1',
        }
        self.authorized_test_user.post(
            reverse('posts:add_comment', kwargs={'post_id': 2}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.get(id=1).text,
                         'Тестовый комментарий 1')
        self.assertEqual(Comment.objects.latest('id').id, 1)
        form_data = {
            'text': 'Тестовый комментарий 2',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 2}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.latest('id').id, 1)
