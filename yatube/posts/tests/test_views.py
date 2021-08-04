import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Test')
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
        cls.group = Group.objects.create(
            title='Тестовое имя группы',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Текст' * 100,
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'edit.html': reverse('new_post'),
            'group.html': (
                reverse('group', kwargs={'slug': self.group.slug})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        object = response.context['page'][0]
        post_text = object.text
        post_author = object.author
        post_image = object.image
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author.username, self.post.author.username)
        self.assertEqual(post_image, self.post.image)

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        object = response.context['group']
        img_object = response.context['page'][0]
        group_title = object.title
        group_description = object.description
        group_slug = object.slug
        post_image = img_object.image
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_description, self.group.description)
        self.assertEqual(group_slug, self.group.slug)
        self.assertEqual(post_image, self.post.image)

    def test_new_post_shows_correct_context(self):
        """Шаблон edit для new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_shows_correct_context(self):
        """Шаблон edit для post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={
                'username': self.post.author.username,
                'post_id': self.post.id
            })
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user.username})
        )
        object = response.context['author']
        author_username = object.username
        img_object = response.context['page'][0]
        post_image = img_object.image
        self.assertEqual(author_username, self.user.username)
        self.assertEqual(post_image, self.post.image)

    def test_profile_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post', kwargs={
                'username': self.user.username,
                'post_id': self.post.id,
            })
        )
        object = response.context['author']
        author_username = object.username
        img_object = response.context['post']
        post_image = img_object.image
        self.assertEqual(author_username, self.post.author.username)
        self.assertEqual(post_image, self.post.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test')
        i = 0
        while i < 13:
            Post.objects.create(
                text=f'Текст{i}' * 50,
                author=cls.user,
            )
            i += 1

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context['page']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context['page']), 3)


class NewPostGroupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test')
        i = 1
        cls.group = []
        while i <= 2:
            cls.group.append(Group.objects.create(
                title=f'Тестовое имя группы{i}',
                slug=f'test-group{i}',
                description=f'Тестовое описание группы{i}'
            ))
            i += 1
        cls.group = tuple(cls.group)
        cls.post = Post.objects.create(
            text='Текст' * 100,
            author=cls.user,
            group=cls.group[0]
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_shows_correct_post_group(self):
        slug_group1 = self.group[0].slug
        slug_group2 = self.group[1].slug
        reverses = [
            reverse('index'),
            reverse('group', kwargs={'slug': slug_group1})
        ]
        for rev in reverses:
            with self.subTest(rev=rev):
                response = self.authorized_client.get(rev)
                object = response.context['page'][0]
                post_text = object.text
                post_author = object.author
                post_group = object.group.slug
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(
                    post_author.username, self.post.author.username
                )
                self.assertEqual(post_group, slug_group1)
                self.assertNotEqual(post_group, slug_group2)


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """URLы, генерируемые при помощи имен доступны."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)

    def test_about_page_uses_correct_template(self):
        """При запросе к author
        применяется шаблон ../templates/about/author.html."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')
        response = self.guest_client.get(reverse('about:tech'))
        self.assertTemplateUsed(response, 'about/tech.html')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user_follower = User.objects.create_user(username='Follower')
        cls.user_silent = User.objects.create_user(username='Silent')
        cls.post_1 = Post.objects.create(
            text='Текст' * 10,
            author=cls.user_author
        )
        cls.post_2 = Post.objects.create(
            text='Тишина' * 10,
            author=cls.user_silent
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_follower)

    def test_authorized_client_can_follow_unfollow(self):
        """Авторизованный пользователь может подписаться и отписаться."""
        follows_count = Follow.objects.count()
        # Подписывается
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.user_author.username})
        )
        self.assertEqual(follows_count + 1, Follow.objects.count())
        # Отписывается
        self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': self.user_author.username})
        )
        self.assertEqual(follows_count, Follow.objects.count())

    def test_new_post_authorized_client_in_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.
        """
        # Подписывается
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': self.user_author.username})
        )
        response = self.authorized_client.get(reverse('follow_index'))
        object = response.context['page'][0]
        post_author = object.author
        self.assertEqual(
            post_author.username, self.post_1.author.username
        )
        self.assertNotEqual(
            post_author.username, self.post_2.author.username
        )


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.user_commentator = User.objects.create_user(username='Commentator')
        cls.post = Post.objects.create(
            text='Текст' * 10,
            author=cls.user_author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_commentator)

    def test_allows_to_comment_posts_guest(self):
        response = self.guest_client.get(
            reverse('add_comment', kwargs={
                'username': self.post.author.username,
                'post_id': self.post.id,
            })
        )
        self.assertEqual(response.status_code, 302)

    def test_allows_to_comment_posts_authorized(self):
        response = self.authorized_client.get(
            reverse('add_comment', kwargs={
                'username': self.post.author.username,
                'post_id': self.post.id,
            })
        )
        self.assertEqual(response.status_code, 200)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test')
        cls.post = Post.objects.create(
            text='TeXt' * 10,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        response = self.authorized_client.get(reverse('index'))
        post_count = len(response.context['page'])
        Post.objects.create(
            text='Second' * 10,
            author=self.user
        )
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(post_count, len(response.context['page']))
