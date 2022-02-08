from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


SYMBOLS_NUMBER = 15


class Group(models.Model):

    title = models.CharField(max_length=200)

    slug = models.SlugField(unique=True)

    description = models.TextField()

    def __str__(self):

        return self.title


class Post(models.Model):

    text = models.TextField(
        verbose_name="Текст поста", help_text="Введите текст поста"
    )

    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="posts",
    )

    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
    )

    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="posts/",
        blank=True,
        help_text="Добавьте картинку",
    )

    def __str__(self):

        return self.text[:SYMBOLS_NUMBER]

    class Meta:

        ordering = ["-pub_date"]


class Comment(models.Model):

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="comments",
    )

    text = models.TextField(
        "Текст комментария", help_text="Введите текст комментария"
    )

    created = models.DateTimeField("Дата публикации", auto_now_add=True)


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
        related_name="follower",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="following",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follower"
            )
        ]
