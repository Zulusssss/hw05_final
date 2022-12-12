from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow
from .utils import paginator
from django.contrib.auth.decorators import login_required

from django.views.decorators.cache import cache_page

NUMBER_OF_POSTS = 10
PAGE_POSTS_OF_USER = 2


@cache_page(20)
def index(request):
    '''
    Позволяет перенести в HTML-код главной страницы сайта записи из
    таблицы "Post" из БД для тега <main> и строку для тега <title>.
    Записи из "Post" отсортированы по убыванию даты публикации.
    Записей взято - первые 10 штук.
    '''
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = paginator(request, post_list, NUMBER_OF_POSTS)
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, slug):
    '''
    Позволяет перенести в HTML-код страницы данной группы постов записи из
    таблицы "Post" из БД для тега <main> и строку для тега <title>.
    Записи из "Post" отсортированы по убыванию даты публикации и соответствуют
    определённой группе, которая оп-ся, исходя из значения "slug".
    Записей взято - первые 10 штук.
    '''
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator(request, posts, NUMBER_OF_POSTS)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    '''
    Переводит на страницу с постами конкретного пользователя.
    '''
    user = User.objects.get(username=username)
    post_list = user.posts.all()
    queryset = Follow.objects.filter(user=request.user.pk,
                                     author=user.pk)
    following = len(queryset) != 0
    number_post_of_user = post_list.count()
    page_obj = paginator(request, post_list, PAGE_POSTS_OF_USER)
    templates = 'posts/profile.html'
    context = {
        'number_post_of_user': number_post_of_user,
        'username': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, templates, context)


def post_detail(request, post_id):
    '''
    Переводит на страницу с информацией конкретного поста.
    Если вы являетесь автором данного поста, то вам будет
    доступна кнопка "редактировать запись".
    '''
    post = Post.objects.get(pk=post_id)
    number_post_of_user = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    comments = post.comments.all()

    templates = 'posts/post_detail.html'
    context = {
        'number_post_of_user': number_post_of_user,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, templates, context)


@login_required
def post_create(request):
    '''
    Переводит на страницу с формой для создания нового поста.
    '''
    groups = Group.objects.all()
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)

        return render(request, 'posts/create_or_up_post.html',
                      {'form': form, 'groups': groups, })

    form = PostForm()
    return render(request, 'posts/create_or_up_post.html',
                  {'form': form, 'groups': groups, })


@login_required
def post_edit(request, post_id):
    '''
    Переводит на страницу редактирования поста.
    '''
    is_edit = True
    post = Post.objects.get(pk=post_id)
    id_author = post.author
    groups = Group.objects.all()
    if id_author == request.user:
        if request.method == 'POST':
            form = PostForm(request.POST, files=request.FILES or None,
                            instance=post)

            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', post_id)

            return render(request, 'posts/create_or_up_post.html',
                          {'form': form, 'post': post,
                           'is_edit': is_edit, 'groups': groups, })

        form = PostForm()
        return render(request, 'posts/create_or_up_post.html',
                      {'form': form, 'post': post,
                       'is_edit': is_edit, 'groups': groups, })

    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    '''
    Создаёт страницу с постами авторов, на которых сделана подписка.
    '''
    set = User.objects.filter(following__in=Follow.objects.
                              filter(user=request.user.pk))
    post_list = Post.objects.select_related('author',
                                            'group').filter(author__in=set)
    page_obj = paginator(request, post_list, NUMBER_OF_POSTS)
    template = 'posts/follow.html'
    title = 'Избранные авторы'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    '''
    Для формирования подписки на автора.
    '''
    if username == request.user.username:
        return redirect('posts:profile', username=username)
    user = get_object_or_404(User, username=username)
    Follow.objects.get_or_create(user=request.user, author=user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    '''
    Для отказа от подписки на автора.
    '''
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect('posts:profile', username=username)
