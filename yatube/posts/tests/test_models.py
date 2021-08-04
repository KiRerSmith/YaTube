from django.test import TestCase
from posts.models import Group, Post, User


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое имя группы',
            slug='test-group',
            description='Тестовое описание группы'
        )

    def test_str_group(self):
        """__str__  group - это строчка с содержимым group.title."""
        group = GroupModelTest.group
        expected_str = group.title
        self.assertEqual(expected_str, str(group))


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        authorized_user = User.objects.create_user(username='Test')
        cls.post = Post.objects.create(
            text='Т' * 20,
            author=authorized_user
        )

    def test_convert_text_to_post_title(self):
        """post title - это строчка с содержимым post.text из 15 симв."""
        post = PostModelTest.post
        title = str(post)
        self.assertEqual(title, 'Т' * 15)

    def test_str_post(self):
        """__str__  post - это строчка с сокращенным post.text."""
        post = PostModelTest.post
        expected_str = post.text[:15]
        self.assertEqual(expected_str, str(post))
