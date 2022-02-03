from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post

        fields = ("text", "group", "image")

        labels = {
            "text": _("Текст поста"),
            "group": _("Группа"),
            "image": _("Картинка"),
        }
        help_texts = {
            "text": _("Текст нового поста"),
            "group": _("Группа, к которой будет относиться пост"),
            "image": _("Добавьте картинку"),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment

        fields = ("text",)
        labels = {
            "text": _("Текст поста"),
        }
        help_texts = {
            "text": _("Новый комментарий"),
        }
