from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import SYMBOLS_NUMBER, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая группа",
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у Post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:SYMBOLS_NUMBER]
        self.assertEqual(expected_object_name, str(post))

    def test_group_have_correct_object_names(self):
        """Проверяем, что у Group корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
