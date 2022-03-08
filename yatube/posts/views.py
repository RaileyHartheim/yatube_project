from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User

POSTS_LIM = 10


# @cache_page(20)
def index(request):
    all_posts = Post.objects.all()
    paginator = Paginator(all_posts, POSTS_LIM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.all()
    paginator = Paginator(group_posts, POSTS_LIM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    post_count = author_posts.count()
    paginator = Paginator(author_posts, POSTS_LIM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = Follow.objects.filter(author=author,
                                          user=request.user).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_author = get_object_or_404(User, username=post.author)
    author_posts = Post.objects.filter(author=post_author).all()
    post_comments = Comment.objects.filter(post=post).all()
    post_count = author_posts.count()
    form = CommentForm()
    context = {
        'post': post,
        'post_author': post_author,
        'post_count': post_count,
        'form': form,
        'post_comments': post_comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@cache_page(20)
@login_required
def follow_index(request):
    authors_ids = Follow.objects.filter(
        user=request.user).values_list('author_id', flat=True)
    posts = Post.objects.filter(author_id__in=authors_ids)
    paginator = Paginator(posts, POSTS_LIM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    following = User.objects.get(username=username)
    if (request.user != following
        and not Follow.objects.filter(author=following,
                                      user=request.user).exists()):
        Follow.objects.create(author=following, user=request.user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = User.objects.get(username=username)
    Follow.objects.filter(author=following, user=request.user).delete()
    return redirect('posts:profile', username=username)
