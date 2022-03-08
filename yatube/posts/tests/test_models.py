from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ian')
        cls.group = Group.objects.create(
            title='Joy Division',
            slug='joy_division',
            description='One English rock band'
        )
        cls.post = Post.objects.create(
            text='This is a crisis I knew had to come',
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        expected_real = {
            self.post.text[:15]: str(self.post),
            self.group.title: str(self.group)
        }
        for expected, real in expected_real.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_verbose_names_are_correct(self):
        post = PostModelTest.post
        post_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in post_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

        group = PostModelTest.group
        group_verboses = {
            'title': 'Название',
            'slug': 'Уникальный идентификатор',
            'description': 'Описание группы'
        }
        for field, expected_value in group_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_texts_are_correct(self):
        post = PostModelTest.post
        post_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'

        }
        for field, expected_value in post_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

        group = PostModelTest.group
        group_help_text = {
            'title': 'Назовите группу',
            'slug': 'Укажите идентификатор для URL',
            'description': 'Опишите группу'
        }
        for field, expected_value in group_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value
                )
