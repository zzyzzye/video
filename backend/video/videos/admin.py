from django.contrib import admin
from .models import Category, Tag, Video, VideoLike, Comment, VideoView


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'is_published', 
                   'views_count', 'likes_count', 'comments_count', 'created_at')
    list_filter = ('status', 'is_published', 'category')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('views_count', 'likes_count', 'comments_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'video__title')
    ordering = ('-created_at',)
    raw_id_fields = ('user', 'video')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'parent', 'text', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'video__title', 'text')
    ordering = ('-created_at',)
    raw_id_fields = ('user', 'video', 'parent')


@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'ip_address', 'watched_duration', 'view_date')
    list_filter = ('view_date',)
    search_fields = ('user__username', 'video__title', 'ip_address')
    ordering = ('-view_date',)
    raw_id_fields = ('user', 'video')
