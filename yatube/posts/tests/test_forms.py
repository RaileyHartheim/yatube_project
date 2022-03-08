import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USERNAME = 'testuser'
        cls.GROUP_TITLE = 'Test group'
        cls.SLUG = 'test_group'
        cls.GROUP_DESCRIPTION = 'Description of test group'
        cls.TEXT = 'Text of test post'
        cls.EDITED_TEXT = 'Edited text of test post'
        cls.CREATED_TEXT = 'Created text of test post'
        cls.ADDRESSES = [
            reverse('posts:profile', kwargs={'username': cls.USERNAME}),
            reverse('posts:post_create')
        ]
        cls.INDEX = reverse('posts:index')
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.USERNAME}
        )
        cls.GROUP_LIST = reverse(
            'posts:group_list',
            kwargs={'slug': cls.SLUG}
        )
        cls.POST_CREATE = reverse('posts:post_create')
        cls.user = User.objects.create_user(username=cls.USERNAME)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.SLUG,
            description=cls.GROUP_DESCRIPTION
        )
        cls.premade_post = Post.objects.create(
            text='Text of test post',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': self.CREATED_TEXT,
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            self.ADDRESSES[1],
            data=form_data
        )
        self.assertRedirects(response, self.ADDRESSES[0])
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.CREATED_TEXT,
                author=self.user,
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {'text': self.EDITED_TEXT, 'group': self.group.id}
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.premade_post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.premade_post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=self.EDITED_TEXT
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                text=self.CREATED_TEXT
            )
        )

    def test_guest_has_no_access_to_post_creation(self):
        posts_count = Post.objects.count()
        form_data = {'text': self.CREATED_TEXT}
        response = self.guest_client.post(
            self.ADDRESSES[1],
            data=form_data
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
        self.assertFalse(
            Post.objects.filter(
                text=self.CREATED_TEXT
            ).exists()
        )

    def test_guest_has_no_access_to_post_edit(self):
        form_data = {'text': self.EDITED_TEXT}
        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.premade_post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.premade_post.pk}/edit/'
        )
        self.assertFalse(
            Post.objects.filter(
                text=self.EDITED_TEXT
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                text=self.premade_post.text
            ).exists()
        )
