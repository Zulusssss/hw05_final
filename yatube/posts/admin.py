from django.contrib import admin

from .models import Post, Group, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    '''
    Класс для настройки отображения модели Post в интерфейсе админки.
    '''
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    '''
    Класс для настройки отображения модели Group в интерфейсе админки.
    '''
    pass


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    '''
    Класс для настройки отображения модели Follow в интерфейсе админки.
    '''
    pass
