from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.another_user = User.objects.create_user(username='anothertestuser')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='Description of test group'
        )
        cls.post = Post.objects.create(
            text='Text of test post',
            author=cls.user,
            group=cls.group
        )
        cls.pages_for_author = [
            '/',
            f'/profile/{cls.user.username}/',
            f'/group/{cls.group.slug}/',
            f'/posts/{cls.post.pk}/',
            '/create/',
            f'/posts/{cls.post.pk}/edit/'
        ]
        cls.pages_for_not_author = [
            '/',
            f'/profile/{cls.user.username}/',
            f'/group/{cls.group.slug}/',
            f'/posts/{cls.post.pk}/',
            '/create/',
        ]
        cls.pages_for_guest = [
            '/',
            f'/profile/{cls.user.username}/',
            f'/group/{cls.group.slug}/',
            f'/posts/{cls.post.pk}/',
        ]
        cls.pages_redirect_for_guest = [
            '/create/',
            f'/posts/{cls.post.pk}/edit/',
        ]
        cls.urls_templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client = Client()
        self.another_client.force_login(self.another_user)
        self.clients = [
            self.authorized_client,
            self.another_client,
            self.guest_client
        ]
        cache.clear()

    def test_all_urls_exist_for_post_author(self):
        for address in self.pages_for_author:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_urls_exist_for_not_author_except_for_edit(self):
        for address in self.pages_for_not_author:
            with self.subTest(address=address):
                response = self.another_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirects_for_not_author(self):
        response = self.another_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_all_urls_for_not_authorized_exist_for_guest(self):
        for address in self.pages_for_guest:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_and_edit_urls_redirect_for_guest(self):
        for address in self.pages_redirect_for_guest:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_not_found_for_all_users(self):
        for client in self.clients:
            with self.subTest(client=client):
                response = self.client.get('/unexisting_page/')
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_use_correct_templates(self):
        for address, template in self.urls_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
