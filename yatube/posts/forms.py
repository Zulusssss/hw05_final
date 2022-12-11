from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    '''
    Класс формы для создания формы создания/редактирования записи.
    Связан с моделью Post.
    '''
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': ('Текст поста'),
            'group': ('Необязательная группа, к которой можно отнести пост'),
            'image': ('Необязательная картинка к посту'),
        }


class CommentForm(forms.ModelForm):
    '''
    Создаёт форму для создания комментария к посту.
    Связан с моделью Post.
    '''
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': ('Текст комментария к посту'),
        }
