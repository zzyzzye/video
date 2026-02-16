from django.contrib import admin
from .models import ModerationResult, FrameRecognition, VideoSummary


@admin.register(ModerationResult)
class ModerationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'status', 'result', 'confidence', 'created_at']
    list_filter = ['status', 'result', 'created_at']
    search_fields = ['video__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('video', 'status', 'result', 'confidence')
        }),
        ('评分详情', {
            'fields': ('neutral_score', 'low_score', 'medium_score', 'high_score')
        }),
        ('问题帧', {
            'fields': ('flagged_frames',)
        }),
        ('其他信息', {
            'fields': ('details', 'error_message', 'created_at', 'updated_at')
        }),
    )


@admin.register(FrameRecognition)
class FrameRecognitionAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'timestamp', 'scene', 'confidence', 'created_at']
    list_filter = ['scene', 'created_at']
    search_fields = ['video__title', 'text_content']
    readonly_fields = ['created_at']


@admin.register(VideoSummary)
class VideoSummaryAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'scene_changes', 'created_at']
    search_fields = ['video__title', 'summary']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('video', 'summary')
        }),
        ('关键信息', {
            'fields': ('key_frames', 'auto_tags', 'scene_changes', 'dominant_colors')
        }),
        ('详细信息', {
            'fields': ('details', 'created_at', 'updated_at')
        }),
    )
