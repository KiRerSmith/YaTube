import random
import string

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_page_not_found(self):
        rnds = ''.join([random.choice(string.ascii_letters) for i in range(9)])
        response = self.guest_client.get(f'/{rnds}/')
        self.assertEqual(response.status_code, 404)


class YaTubeURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-group'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.new_user = User.objects.create_user(username='NewUser')
        self.new_authorized_client = Client()
        self.new_authorized_client.force_login(self.new_user)
        Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )
        post = Post.objects.get(text='Тестовый пост')
        self.templates_url_names = {
            'index.html': '/',
            'group.html': f'/group/{self.group.slug}/',
            'edit.html': '/new/',
            'profile.html': f'/{post.author}/',
            'post.html': f'/{post.author}/{post.id}/',
            'follow.html': '/follow/',
        }
        self.no_redirect_urls = {
            '/': '/',
            '/group/test-group/': f'/group/{self.group.slug}/',
        }
        self.redirect_urls = {
            '/new/': '/auth/login/?next=/new/',
        }

    def test_urls_uses_correct_template(self):
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_authorized_client(self):
        for adress in self.templates_url_names.values():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_urls_guest_client_with_no_redirects(self):
        for request_adress in self.no_redirect_urls.values():
            with self.subTest(request_adress=request_adress):
                response = self.guest_client.get(request_adress)
                self.assertEqual(response.status_code, 200)

    def test_urls_guest_client_with_redirects(self):
        for request_adress, redirect_adress in self.redirect_urls.items():
            with self.subTest(request_adress=request_adress):
                response = self.guest_client.get(request_adress)
                self.assertRedirects(response, redirect_adress)

    def test_post_edit_url_different_clients(self):
        """Проверяет доступность страницы редактирования поста"""
        post = Post.objects.get(text='Тестовый пост')
        adress = f'/{post.author}/{post.id}/edit/'
        # Для анонимного пользователя
        response_guest = self.guest_client.get(adress, follow=True)
        self.assertRedirects(
            response_guest, (f'/auth/login/?next={adress}')
        )
        # Для авторизованного пользователя — не автора поста
        response_logined = self.new_authorized_client.get(adress, follow=True)
        self.assertRedirects(
            response_logined, (f'/{post.author}/{post.id}/')
        )
        # Для авторизованного пользователя — автора поста
        response_author = self.authorized_client.get(adress)
        self.assertEqual(response_author.status_code, 200)
