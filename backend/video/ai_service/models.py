from django.db import models
from videos.models import Video


class ModerationResult(models.Model):
    """AI 内容审核结果"""
    
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('processing', '审核中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    RESULT_CHOICES = [
        ('safe', '安全'),
        ('unsafe', '不安全'),
        ('uncertain', '不确定'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='ai_moderations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, null=True, blank=True)
    confidence = models.FloatField(default=0.0, help_text='置信度 0-1')
    
    # 各类别得分
    nsfw_score = models.FloatField(default=0.0, help_text='NSFW 内容得分')
    violence_score = models.FloatField(default=0.0, help_text='暴力内容得分')
    sensitive_score = models.FloatField(default=0.0, help_text='敏感内容得分')
    
    # 标记的问题帧
    flagged_frames = models.JSONField(default=list, blank=True, help_text='问题帧时间戳列表')
    
    # 详细信息
    details = models.JSONField(default=dict, blank=True, help_text='详细审核信息')
    error_message = models.TextField(blank=True, help_text='错误信息')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_moderation_result'
        ordering = ['-created_at']
        verbose_name = 'AI审核结果'
        verbose_name_plural = 'AI审核结果'
    
    def __str__(self):
        return f"Moderation for Video {self.video_id} - {self.result}"


class FrameRecognition(models.Model):
    """画面识别结果"""
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='frame_recognitions')
    timestamp = models.FloatField(help_text='视频时间戳（秒）')
    
    # 识别结果
    detected_objects = models.JSONField(default=list, help_text='识别到的物体列表')
    scene = models.CharField(max_length=100, blank=True, help_text='场景分类')
    text_content = models.TextField(blank=True, help_text='OCR 识别的文字')
    faces = models.JSONField(default=list, help_text='人脸信息')
    
    confidence = models.FloatField(default=0.0, help_text='整体置信度')
    details = models.JSONField(default=dict, blank=True, help_text='详细识别信息')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_frame_recognition'
        ordering = ['-created_at']
        verbose_name = '画面识别'
        verbose_name_plural = '画面识别'
        indexes = [
            models.Index(fields=['video', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Frame Recognition for Video {self.video_id} at {self.timestamp}s"


class VideoSummary(models.Model):
    """视频摘要"""
    
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='ai_summary')
    
    summary = models.TextField(help_text='视频内容摘要')
    key_frames = models.JSONField(default=list, help_text='关键帧时间戳列表')
    auto_tags = models.JSONField(default=list, help_text='AI 生成的标签')
    
    # 统计信息
    scene_changes = models.IntegerField(default=0, help_text='场景切换次数')
    dominant_colors = models.JSONField(default=list, help_text='主要颜色')
    
    details = models.JSONField(default=dict, blank=True, help_text='详细摘要信息')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_video_summary'
        verbose_name = '视频摘要'
        verbose_name_plural = '视频摘要'
    
    def __str__(self):
        return f"Summary for Video {self.video_id}"
