from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.NUMBER_OF_BLOCKS)
    page_number = request.GET.get('page')
    if page_number == 1 or page_number is None:
        page = cache.get('index_page')
        if page is None:
            page = paginator.get_page(page_number)
            cache.set('index_page', page, timeout=20)
        return render(request, 'index.html', {'page': page})
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.NUMBER_OF_BLOCKS)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.NUMBER_OF_BLOCKS)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    followers = author.following.all().values('user_id')
    following = False
    self_follower = False
    if request.user == author:
        self_follower = True
    if followers:
        try:
            follower_id = followers.get(user_id=request.user.id)['user_id']
            if follower_id == request.user.id:
                following = True
        except ObjectDoesNotExist:
            pass
    followers_statics = {
        'followers_count': author.following.all().count(),
        'follows_count': author.follower.all().count(),
    }
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'following': following,
        'followers_statics': followers_statics,
        'self_follower': self_follower
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    followers_statics = {
        'followers_count': author.following.filter(
            author__username=username).count(),
        'follows_count': author.follower.all().count(),
    }
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    return render(request, 'post.html', {
        'form': form,
        'author': author,
        'post': post,
        'comments': comments,
        'followers_statics': followers_statics,
        'add_comment': False
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'edit.html', {'form': form})


@login_required
def post_edit(request, post_id, username):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    if request.user == author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            post.save()
            return redirect('post', request.user, post.id)
        return render(
            request, 'edit.html',
            {'form': form, 'post': post, 'edit': True})
    return redirect('post', author, post.id)


@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', author, post.id)
    return render(request, 'post.html', {
        'form': form,
        'author': author,
        'post': post,
        'comments': comments,
        'add_comment': True
    })


@login_required
def follow_index(request):
    followings = request.user.follower.all().values('author_id')
    followings_id = []
    for items in list(followings):
        followings_id += [items['author_id']]
    post_list = Post.objects.filter(author__id__in=followings_id)
    paginator = Paginator(post_list, settings.NUMBER_OF_BLOCKS)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    # if username != request.user.username:
    if not Follow.objects.filter(
        user=request.user,
        author=author
    ).exists() and username != request.user.username:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if username != request.user.username:
        author.following.filter(user__username=request.user.username).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
