from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm
from ..models import Comment, Group, Post, User


class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USERNAME = 'testuser'
        cls.GROUP_TITLE = 'Test group'
        cls.SLUG = 'test_group'
        cls.GROUP_DESCRIPTION = 'Description of test group'
        cls.TEXT = 'Text of test post'
        cls.user = User.objects.create_user(username=cls.USERNAME)
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.SLUG,
            description=cls.GROUP_DESCRIPTION
        )
        cls.post = Post.objects.create(
            text='Text of test post',
            author=cls.user,
            group=cls.group
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'this is comment'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='this is comment',
                post=self.post,
                author=self.user
            ).exists()
        )

    def test_guest_has_no_access_to_comment_addition(self):
        comment_count = Comment.objects.count()
        form_data = {'text': 'this is another comment'}
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
        self.assertNotEqual(Comment.objects.count(), comment_count + 1)
        self.assertFalse(
            Post.objects.filter(
                text='this is another comment'
            ).exists()
        )
