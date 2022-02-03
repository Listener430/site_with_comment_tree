import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            id=65, author=cls.user, group=cls.group, image=cls.image
        )

        cls.form = PostForm()
        cls.form_comment = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.guest_user = PostCreateFormTests.user
        self.guest_user2 = PostCreateFormTests.user2
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.guest_user)
        self.authorized_client2.force_login(self.guest_user2)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()

        form_data = {
            "author": self.user.id,
            "group": self.group.id,
            "text": "1",
            "image": SimpleUploadedFile(
                name="big.gif",
                content=self.small_gif,
                content_type="image/gif",
            ),
        }

        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )

        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": "HasNoName"}),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text="1",
                group=self.group.id,
                author=self.user.id,
                image="posts/big.gif",
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактируем запись в Post."""
        tasks_count = Post.objects.count()
        form = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": 65})
        ).context["form"]
        form_data = form.initial
        form_data["text"] = "testing_test"
        form_data["group"] = self.group2.id
        form_data["image"] = SimpleUploadedFile(
            name="large.gif",
            content=self.small_gif,
            content_type="image/gif",
        )

        self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": 65}),
            data=form_data,
            follow=True,
        )
        self.post65.refresh_from_db()
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count)
        # Проверяем, что создалась запись с заданными полями
        self.assertEqual(self.post65.text, "testing_test")
        self.assertEqual(self.post65.group, self.group2)
        self.assertEqual(self.post65.image, "posts/large.gif")
        # форма перенаправляет неавтора
        self.assertRedirects(
            self.authorized_client2.get("/posts/65/edit/", follow=True),
            "/posts/65/",
        )
        # Проверяем, что она исчезла из старой группы
        response = self.authorized_client.get("/group/test-slug/")
        self.assertNotIn(self.post65, response.context["page_obj"])

    def test_post_comment(self):
        """Валидная форма создает коммент в Post.."""
        form_data = {
            "author": self.user.id,
            "post": self.post65,
            "text": "comment",
        }

        self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": 65}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(
                text="comment", author=self.user.id, post=self.post65
            ).exists()
        )
