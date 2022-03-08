from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USERNAME = 'testuser'
        cls.GROUP_TITLE = 'Test group'
        cls.SLUG = 'test_group'
        cls.GROUP_DESCRIPTION = 'Description of test group'
        cls.TEXT = 'Text of test post'
        cls.PAGES_ADDRESSES = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': cls.USERNAME}),
            reverse('posts:group_list', kwargs={'slug': cls.SLUG})
        ]
        cls.PAGINATOR_NUMBER = 13
        cls.FIRST_PAGE_COUNT_POSTS = 10
        cls.SECOND_PAGE_COUNT_POSTS = 3
        cls.user = User.objects.create_user(username=cls.USERNAME)
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug=cls.SLUG,
            description=cls.GROUP_DESCRIPTION
        )
        for i in range(cls.PAGINATOR_NUMBER):
            cls.post = Post.objects.create(
                text=cls.TEXT,
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_pages_with_paginator_contain_right_amount_of_records(self):
        for address in self.PAGES_ADDRESSES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.FIRST_PAGE_COUNT_POSTS
                )
                response = self.authorized_client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.SECOND_PAGE_COUNT_POSTS
                )

    def test_second_pages_with_paginator_contain_right_amount_of_records(self):
        for address in self.PAGES_ADDRESSES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.SECOND_PAGE_COUNT_POSTS
                )
