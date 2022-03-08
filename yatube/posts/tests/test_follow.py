from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = User.objects.create_user(username='alice')
        cls.bert = User.objects.create_user(username='bert')
        cls.cecil = User.objects.create_user(username='cecil')
        cls.dan = User.objects.create_user(username='dan')
        cls.addresses = [
            reverse('posts:profile', kwargs={'username': cls.alice.username}),
            reverse('posts:profile', kwargs={'username': cls.bert.username}),
            reverse('posts:profile', kwargs={'username': cls.cecil.username}),
            reverse('posts:profile', kwargs={'username': cls.dan.username}),
            reverse('posts:profile_follow',
                    kwargs={'username': cls.bert.username}),
            reverse('posts:profile_follow',
                    kwargs={'username': cls.cecil.username}),
            reverse('posts:profile_unfollow',
                    kwargs={'username': cls.bert.username}),
            reverse('posts:profile_unfollow',
                    kwargs={'username': cls.cecil.username}),
            reverse('posts:follow_index'),
            reverse('posts:profile_unfollow',
                    kwargs={'username': cls.dan.username}),
        ]
        cls.group = Group.objects.create(
            title='just group',
            slug='just_group'
        )
        cls.bert_post = Post.objects.create(
            text="this is Bert's post",
            author=cls.bert,
            group=cls.group
        )
        cls.cecil_post = Post.objects.create(
            text="this is Cecil's post",
            author=cls.cecil,
            group=cls.group
        )
        cls.follow_dan_cecil = Follow.objects.create(
            user=cls.dan, author=cls.cecil
        )

    def setUp(self):
        self.alice_client = Client()
        self.alice_client.force_login(self.alice)
        self.dan_client = Client()
        self.dan_client.force_login(self.dan)

    def test_authorized_client_can_follow_other_users(self):
        follow_count = Follow.objects.count()
        response = self.alice_client.get(self.addresses[4])
        self.assertRedirects(response, self.addresses[1])
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.alice,
                author=self.bert
            ).exists()
        )

    def test_authorized_client_can_unfollow_other_users(self):
        response = self.alice_client.get(self.addresses[5])
        follow_count = Follow.objects.count()
        response = self.alice_client.get(self.addresses[7])
        self.assertRedirects(response, self.addresses[2])
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.alice,
                author=self.cecil
            ).exists()
        )

    def test_authorized_client_cant_follow_themself(self):
        follow_count = Follow.objects.count()
        response = self.dan_client.get(self.addresses[9])
        self.assertRedirects(response, self.addresses[3])
        self.assertNotEqual(Follow.objects.count(), follow_count + 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.dan,
                author=self.dan
            ).exists()
        )

    def test_only_following_posts_show_in_follow_index(self):
        self.follow_alice_bert = Follow.objects.create(
            user=self.alice, author=self.bert
        )
        response = self.alice_client.get(reverse('posts:follow_index'))
        self.assertIn(self.bert_post, response.context['page_obj'])
        self.assertNotIn(self.cecil_post, response.context['page_obj'])
