import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post
from posts.views import POST_NUMBER

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

PAGINATOR_TEST = 3


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="HasNoName")
        cls.user2 = User.objects.create_user(username="Another")
        cls.group = Group.objects.create(
            slug="test-slug",
        )
        cls.group2 = Group.objects.create(
            slug="undesirable1",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.image = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post65 = Post.objects.create(
            id=65,
            text="tt",
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )
        cls.post66 = Post.objects.create(
            id=66,
            text="tb",
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )
        cls.post67 = Post.objects.create(
            id=67,
            text="tz",
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.guest_user = PostPagesTests.user
        self.guest_user2 = PostPagesTests.user2
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.guest_user)
        self.authorized_client2.force_login(self.guest_user2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        urls = (
            ("posts:index", "posts/index.html", None),
            ("about:author", "about/author.html", None),
            ("about:tech", "about/tech.html", None),
            (
                "posts:group_posts",
                "posts/group_list.html",
                {"slug": "test-slug"},
            ),
            ("posts:profile", "posts/profile.html", {"username": "HasNoName"}),
            ("posts:post_detail", "posts/post_detail.html", {"post_id": 65}),
            ("posts:post_create", "posts/create_post.html", None),
            ("posts:post_edit", "posts/create_post.html", {"post_id": 65}),
        )

        for name, template, kwargs in urls:
            with self.subTest(template=template):
                response = self.authorized_client.get(
                    reverse(name, kwargs=kwargs)
                )
                self.assertTemplateUsed(response, template)

    def test_post_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get("/")
        self.assertIn("page_obj", response.context)
        self.assertEqual(
            Post.objects.first().image,
            response.context["page_obj"].object_list[0].image,
        )

    def test_post_group_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:group_posts", kwargs={"slug": "test-slug"})
        )
        group = get_object_or_404(Group, slug="test-slug")
        posts = Post.objects.filter(group=group)
        self.assertIn("page_obj", response.context)
        self.assertEqual(
            list(posts),
            response.context["page_obj"].object_list[0:POST_NUMBER],
        )
        self.assertQuerysetEqual(
            posts,
            Post.objects.filter(
                id__in=(
                    p.id
                    for p in response.context["page_obj"].object_list[
                        0:POST_NUMBER
                    ]
                )
            ),
            transform=lambda x: x,
        )

        self.assertEqual(
            Post.objects.first().image,
            response.context["page_obj"].object_list[0].image,
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": "HasNoName"})
        )
        posts = Post.objects.filter(author=self.guest_user)
        self.assertIn("page_obj", response.context)
        self.assertEqual(
            list(posts),
            response.context["page_obj"].object_list[0:POST_NUMBER],
        )
        self.assertEqual(
            Post.objects.first().image,
            response.context["page_obj"].object_list[0].image,
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get("/posts/65/")
        post = Post.objects.get(id=65)
        self.assertIn("post", response.context)
        self.assertEqual(post, response.context["post"])
        self.assertEqual(post.image, response.context["post"].image)

    def test_post_form_create_show_correct_context(self):
        """Шаблон form_create сформирован с правильным контекстом."""
        response = self.authorized_client.get("/create/")
        self.assertIn("form", response.context)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": 65})
        )
        self.assertIn("form", response.context)
        self.assertEqual(
            self.post65.text, response.context[0]["form"].initial["text"]
        )

    def test_post_exists_3_pages(self):
        """Проверяем, что пост появился на 3-х страницах"""
        urls = [
            "/group/test-slug/",
            "/profile/HasNoName/",
        ]
        posts = Post.objects.all()
        for addres in urls:
            with self.subTest(addres=addres):
                self.assertIn(
                    "page_obj", self.authorized_client.get(addres).context
                )
                self.assertEqual(
                    list(posts),
                    self.authorized_client.get(addres)
                    .context["page_obj"]
                    .object_list[0:POST_NUMBER],
                )

    def test_post_exists_index_page(self):
        """Проверяем, что пост появился на index"""
        posts = Post.objects.all()
        self.assertIn("page_obj", self.authorized_client.get("/").context)
        self.assertEqual(
            list(posts),
            list(
                self.authorized_client.get("/")
                .context["page_obj"]
                .object_list[0:POST_NUMBER]
            ),
        )

    def test_post_notexists_group_page(self):
        """Проверяем, что пост НЕ появился в чужой группе"""
        response = self.authorized_client.get("/group/undesirable1/")
        self.assertNotIn(self.post65, response.context["page_obj"])

    def test_cache_works(self):
        """Проверяем, что кэш работает на главной странице"""
        response = self.authorized_client.get("/")
        content = response.content
        Post.objects.filter(id=67).delete()
        response = self.authorized_client.get("/")
        new_content = response.content
        self.assertEqual(content, new_content)
        cache.clear()
        response = self.authorized_client.get("/")
        clear_content = response.content
        self.assertNotEqual(content, clear_content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.user2 = User.objects.create_user(username="Another")
        cls.follow = Follow.objects.create(author=cls.user, user=cls.user2)
        cls.post = Post.objects.create(id=1, author=cls.user)

    def setUp(self):
        self.guest_client = Client()
        self.guest_user = FollowTests.user
        self.guest_user2 = FollowTests.user2
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.guest_user)
        self.authorized_client2.force_login(self.guest_user2)

    def test_follow_show_correct_context(self):
        """Новая запись пользователя появляется в ленте тех,"""
        """ кто на него подписан и"""
        """не появляется в ленте тех, кто не подписан"""
        response = self.authorized_client2.get("/follow/")
        self.assertEqual(
            Post.objects.first(),
            response.context["page_obj"].object_list[0],
        )
        response = self.authorized_client.get("/follow/")
        self.assertNotIn(
            Post.objects.first(),
            response.context["page_obj"],
        )

    def test_follow_suscribe_unsuscribe(self):
        """Проверяем что пользователь может отписаться,"""
        """и подписаться обратно"""
        count_sucribed = Follow.objects.count()
        self.authorized_client2.get("/profile/HasNoName/unfollow/")
        count_unsucribed = Follow.objects.count()
        self.assertEqual(count_sucribed - 1, count_unsucribed)
        self.authorized_client2.get("/profile/HasNoName/follow/")
        count_sucribed2 = Follow.objects.count()
        self.assertEqual(count_sucribed2 - 1, count_unsucribed)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.group = Group.objects.create(slug="test-slug")

    def setUp(self):
        self.guest_client = Client()
        self.guest_user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest_user)
        for i in range(PAGINATOR_TEST + POST_NUMBER):
            post = ""
            post = post + str(i)
            self.post = Post.objects.create(
                id=i,
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group,
                text=str(i),
            )

    def test_index_first_page_contains_ten_records(self):
        """Тестируем все паджинаторы 3 - штуки"""
        response = self.authorized_client.get("/")
        self.assertEqual(len(response.context["page_obj"]), POST_NUMBER)

    def test_index_second_page_contains_three_records(self):
        response = self.authorized_client.get("/" + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), PAGINATOR_TEST)

    def test_group_first_page_contains_ten_records(self):
        response = self.authorized_client.get("/group/test-slug/")
        self.assertEqual(len(response.context["page_obj"]), POST_NUMBER)

    def test_group_second_page_contains_three_records(self):
        response = self.authorized_client.get("/group/test-slug/" + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), PAGINATOR_TEST)

    def test_profile_first_page_contains_ten_records(self):
        response = self.authorized_client.get("/profile/HasNoName/")
        self.assertEqual(len(response.context["page_obj"]), POST_NUMBER)

    def test_profile_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            "/profile/HasNoName/" + "?page=2"
        )
        self.assertEqual(len(response.context["page_obj"]), PAGINATOR_TEST)
