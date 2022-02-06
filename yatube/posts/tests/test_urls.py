from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.user2 = User.objects.create_user(username="Another")
        cls.group = Group.objects.create(slug="test-slug")
        cls.post = Post.objects.create(id=65, author=cls.user, group=cls.group)

    def setUp(self):
        self.guest_client = Client()
        self.guest_user = StaticURLTests.user
        self.guest_user2 = StaticURLTests.user2
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.guest_user)
        self.authorized_client2.force_login(self.guest_user2)

    def test_urls_exist_at_desired_location(self):
        """Проверяем общедоступные страницы (без автора и авторизации)"""
        addres_names = [
            "/",
            "/about/author/",
            "/about/tech/",
            "/group/test-slug/",
            "/profile/HasNoName/",
            "/posts/65/",
        ]
        for addres in addres_names:
            with self.subTest(addres=addres):
                self.assertEqual(
                    self.guest_client.get(addres).status_code, HTTPStatus.OK
                )

    def test_post_create_url_exists_at_desired_location(self):
        """Страница /create/,/edit/,,доступны авторизованному пользователю."""
        addres_names = [
            "/create/",
            "/posts/65/edit/",
            "/posts/65/comment/",
        ]
        for addres in addres_names:
            with self.subTest(addres=addres):
                self.assertEqual(
                    self.authorized_client.get(addres).status_code,
                    HTTPStatus.OK,
                )

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ недоступна авторизованному автору."""
        response = self.authorized_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ или /edit/ или /comment/ перенаправит анонимного
        пользователя на страницу логина.
        """
        address_dict = {
            "/create/": "/auth/login/?next=/create/",
            "/posts/65/edit/": "/auth/login/?next=/posts/65/edit/",
            "/posts/65/comment/": "/auth/login/?next=/posts/65/comment/",
        }
        for addres, redirect in address_dict.items():
            with self.subTest(addres=addres):
                self.assertRedirects(
                    self.guest_client.get(addres, follow=True), redirect
                )

    def test_post_edit_url_redirect_notauthor_on_admin_login(self):
        """Страница по адресу /edit/ перенаправит
        не автора на страницу просмотра поста."""
        response = self.authorized_client2.get("/posts/65/edit/", follow=True)
        self.assertRedirects(response, "/posts/65/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
            "/group/test-slug/": "posts/group_list.html",
            "/profile/HasNoName/": "posts/profile.html",
            "/posts/65/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            "/posts/65/edit/": "posts/create_post.html",
            "/404page/": "core/404.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
