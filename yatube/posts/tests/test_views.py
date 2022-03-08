import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USERNAME = 'testuser'
        cls.GROUP_TITLE = 'Test group'
        cls.SLUG = 'test_group'
        cls.GROUP_DESCRIPTION = 'Description of test group'
        cls.OTHER_GR_TITLE = 'Non-target group'
        cls.OTHER_GR_SLUG = 'non_target_group'
        cls.OTHER_GROUP_DESCR = 'Description of nontarget group'
        cls.TEXT = 'Text of test post'
        cls.INDEX = reverse('posts:index')
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.USERNAME}
        )
        cls.GROUP_LIST = reverse('posts:group_list', kwargs={'slug': cls.SLUG})
        cls.POST_CREATE = reverse('posts:post_create')
        cls.PAGINATOR_NUMBER = 13
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
        cls.user = User.objects.create_user(username=cls.USERNAME)
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.SLUG,
            description=cls.GROUP_DESCRIPTION
        )
        cls.another_group = Group.objects.create(
            title=cls.OTHER_GR_TITLE,
            slug=cls.OTHER_GR_SLUG,
            description=cls.OTHER_GROUP_DESCR
        )
        cls.post = Post.objects.create(
            text=cls.TEXT,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_templates(self):
        templates_pages = {
            self.INDEX: 'posts/index.html',
            self.POST_CREATE: 'posts/create_post.html',
            self.PROFILE: 'posts/profile.html',
            self.GROUP_LIST: 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        response = self.authorized_client.get(self.INDEX)
        first_object = response.context['page_obj'][0]
        expected_real = {
            first_object.text: self.post.text,
            first_object.author: self.post.author,
            first_object.group: self.post.group,
            first_object.image: self.post.image
        }
        for expected, real in expected_real.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_create_post_shows_correct_context(self):
        response = self.authorized_client.get(self.POST_CREATE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_shows_correct_context(self):
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        response = self.authorized_client.get(post_edit_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_shows_correct_context(self):
        post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        expected_count = self.user.posts.all().count()
        response = self.authorized_client.get(post_detail_url)
        expected_real = {
            response.context.get('post').text: self.TEXT,
            response.context.get('post').image: self.post.image,
            response.context['post_author']: self.user,
            response.context['post_count']: expected_count
        }
        for expected, real in expected_real.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_profile_shows_correct_context(self):
        response = self.authorized_client.get(self.PROFILE)
        expected_count = self.user.posts.all().count()
        expected_real = {
            response.context['author']: self.user,
            response.context['page_obj'][0]: self.post,
            response.context['page_obj'][0].image: self.post.image,
            response.context['post_count']: expected_count
        }
        for expected, real in expected_real.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_group_list_shows_correct_context(self):
        response = self.authorized_client.get(self.GROUP_LIST)
        expected_real = {
            response.context['group']: self.group,
            response.context['page_obj'][0]: self.post,
            response.context['page_obj'][0].image: self.post.image,
        }
        for expected, real in expected_real.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, real)

    def test_created_post_appears_only_at_right_pages(self):
        new_post = Post.objects.create(
            text='Text of new post',
            author=self.user,
            group=self.group
        )
        right_pages = [self.INDEX, self.GROUP_LIST, self.PROFILE]
        for right_page in right_pages:
            response = self.authorized_client.get(right_page)
            self.assertIn(new_post, response.context['page_obj'])
        wrong_page = reverse(
            'posts:group_list',
            kwargs={'slug': self.OTHER_GR_SLUG}
        )
        response = self.authorized_client.get(wrong_page)
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_cache_is_working_correctly(self):
        response_before = self.authorized_client.get(self.INDEX)
        Post.objects.create(
            text='Is cache working?',
            author=self.user,
            group=self.group
        )
        response_after = self.authorized_client.get(self.INDEX)
        self.assertHTMLEqual(str(response_before), str(response_after))
