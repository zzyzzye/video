from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Category(models.Model):
    """视频分类模型"""
    name = models.CharField(_('分类名称'), max_length=50)
    description = models.TextField(_('分类描述'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('分类')
        verbose_name_plural = _('分类')
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """视频标签模型"""
    name = models.CharField(_('标签名称'), max_length=30)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('标签')
        verbose_name_plural = _('标签')
    
    def __str__(self):
        return self.name


class Video(models.Model):
    """视频模型"""
    STATUS_CHOICES = (
        ('uploading', '上传中'),
        ('pending_subtitle_edit', '等待字幕编辑'),  # 新增：字幕编辑引导功能
        ('processing', '处理中'),
        ('ready', '就绪'),
        ('failed', '失败'),
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    )
    
    title = models.CharField(_('标题'), max_length=100, db_index=True)  # 添加索引：用于搜索
    description = models.TextField(_('描述'), blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos', db_index=True)  # 添加索引：用于分类筛选
    tags = models.ManyToManyField(Tag, blank=True, related_name='videos')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos', db_index=True)  # 添加索引：用于用户视频查询
    
    # 视频文件
    video_file = models.FileField(_('视频文件'), upload_to='videos/uploads/%Y/%m/%d/')
    hls_file = models.CharField(_('HLS文件路径'), max_length=255, blank=True, null=True)
    duration = models.FloatField(_('时长(秒)'), default=0, db_index=True)  # 添加索引：用于时长筛选
    resolution = models.PositiveIntegerField(_('最高分辨率'), default=0, db_index=True)  # 存储最高分辨率的高度值，如 2160(4K), 1440(2K), 1080 等
    
    # 视频技术参数
    width = models.PositiveIntegerField(_('视频宽度'), default=0)
    height = models.PositiveIntegerField(_('视频高度'), default=0)
    aspect_ratio = models.CharField(_('宽高比'), max_length=20, blank=True)  # 如 16:9, 4:3, 9:16
    video_codec = models.CharField(_('视频编码'), max_length=50, blank=True)  # 如 h264, hevc
    audio_codec = models.CharField(_('音频编码'), max_length=50, blank=True)  # 如 aac, mp3
    bitrate = models.PositiveIntegerField(_('总码率(kbps)'), default=0)
    video_bitrate = models.PositiveIntegerField(_('视频码率(kbps)'), default=0)
    audio_bitrate = models.PositiveIntegerField(_('音频码率(kbps)'), default=0)
    frame_rate = models.FloatField(_('帧率'), default=0)  # 如 24, 30, 60
    file_size = models.BigIntegerField(_('文件大小(字节)'), default=0)
    
    # 字幕信息
    has_subtitle = models.BooleanField(_('是否有字幕'), default=False, db_index=True)  # 用于筛选有字幕的视频
    subtitle_type = models.CharField(
        _('字幕类型'),
        max_length=20,
        choices=[
            ('none', '无字幕'),
            ('soft', '软字幕'),
            ('hard', '硬字幕'),
        ],
        default='none'
    )
    subtitle_language = models.CharField(_('字幕语言'), max_length=50, blank=True)  # 如 zh, en, zh,en
    subtitle_detected_at = models.DateTimeField(_('字幕检测时间'), null=True, blank=True)

    subtitles_draft = models.JSONField(_('字幕草稿'), default=list, blank=True)
    subtitle_style = models.JSONField(_('字幕样式配置'), default=dict, blank=True, help_text='存储字幕的样式配置（颜色、字体、描边等）')
    
    # 缩略图
    thumbnail = models.ImageField(_('缩略图'), upload_to='videos/thumbnails/%Y/%m/%d/', blank=True, null=True)
    
    # 统计信息
    views_count = models.PositiveIntegerField(_('观看次数'), default=0, db_index=True)  # 添加索引：用于热门排序
    likes_count = models.PositiveIntegerField(_('点赞数'), default=0, db_index=True)  # 添加索引：用于点赞排序
    comments_count = models.PositiveIntegerField(_('评论数'), default=0, db_index=True)  # 添加索引：用于评论排序
    
    # 状态
    status = models.CharField(_('状态'), max_length=30, choices=STATUS_CHOICES, default='uploading', db_index=True)  # 添加索引：用于状态筛选
    is_published = models.BooleanField(_('是否发布'), default=False, db_index=True)  # 添加索引：用于发布状态筛选
    
    # 发布设置
    view_permission = models.CharField(
        _('观看权限'),
        max_length=20,
        choices=[
            ('public', '公开'),
            ('private', '私密'),
            ('fans', '仅粉丝'),
        ],
        default='public',
        db_index=True  # 添加索引：用于权限筛选
    )
    comment_permission = models.CharField(
        _('评论权限'),
        max_length=20,
        choices=[
            ('all', '允许所有人'),
            ('fans', '仅粉丝'),
            ('none', '关闭评论'),
        ],
        default='all'
    )
    allow_download = models.BooleanField(_('允许下载'), default=False)
    enable_danmaku = models.BooleanField(_('开启弹幕'), default=True)
    show_in_profile = models.BooleanField(_('显示在主页'), default=True)
    scheduled_publish_time = models.DateTimeField(_('定时发布时间'), null=True, blank=True, db_index=True)  # 添加索引：用于定时任务查询
    original_type = models.CharField(
        _('原创声明'),
        max_length=20,
        choices=[
            ('original', '原创'),
            ('repost', '转载'),
            ('selfmade', '自制'),
        ],
        default='original'
    )
    
    # 审核相关
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_videos')
    reviewed_at = models.DateTimeField(_('审核时间'), null=True, blank=True)
    review_remark = models.TextField(_('审核备注'), blank=True)
    
    # 时间戳
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True, db_index=True)  # 添加索引：用于时间排序
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    published_at = models.DateTimeField(_('发布时间'), null=True, blank=True, db_index=True)  # 添加索引：用于发布时间排序
    deleted_at = models.DateTimeField(_('删除时间'), null=True, blank=True, db_index=True)  # 软删除标记
    
    class Meta:
        verbose_name = _('视频')
        verbose_name_plural = _('视频')
        ordering = ['-created_at']
        # 添加复合索引：优化常见查询场景
        indexes = [
            # 最新视频查询（状态+创建时间）
            models.Index(fields=['-created_at', 'status', 'is_published'], name='video_latest_idx'),
            # 热门视频查询（播放量+状态）
            models.Index(fields=['-views_count', 'status', 'is_published'], name='video_hot_idx'),
            # 用户视频查询（用户+创建时间）
            models.Index(fields=['user', '-created_at', 'status'], name='video_user_idx'),
            # 分类视频查询（分类+创建时间）
            models.Index(fields=['category', '-created_at', 'status'], name='video_category_idx'),
            # 点赞排序查询
            models.Index(fields=['-likes_count', 'status', 'is_published'], name='video_likes_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_deleted(self):
        """判断视频是否已被软删除"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """软删除视频"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.is_published = False  # 取消发布
        self.save(update_fields=['deleted_at', 'is_published'])
    
    def restore(self):
        """恢复已删除的视频"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])


class VideoLike(models.Model):
    """视频点赞模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_likes')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'video')
        verbose_name = _('视频点赞')
        verbose_name_plural = _('视频点赞')
    
    def __str__(self):
        return f"{self.user.username} likes {self.video.title}"


class Comment(models.Model):
    """评论模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', db_index=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments', db_index=True)  # 添加索引：用于视频评论查询
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', db_index=True)
    text = models.TextField(_('评论内容'))
    is_active = models.BooleanField(_('是否激活'), default=True, db_index=True)  # 添加索引：用于筛选激活评论
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True, db_index=True)  # 添加索引：用于时间排序
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('评论')
        verbose_name_plural = _('评论')
        ordering = ['-created_at']
        # 添加复合索引
        indexes = [
            # 视频评论查询（视频+激活状态+时间）
            models.Index(fields=['video', 'is_active', '-created_at'], name='comment_video_idx'),
            # 用户评论查询
            models.Index(fields=['user', '-created_at'], name='comment_user_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class VideoView(models.Model):
    """视频观看记录模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='video_views', db_index=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='views', db_index=True)
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    user_agent = models.CharField(_('User Agent'), max_length=255, blank=True)
    view_date = models.DateTimeField(_('观看时间'), auto_now_add=True, db_index=True)  # 添加索引：用于时间查询
    watched_duration = models.FloatField(_('观看时长(秒)'), default=0)
    
    class Meta:
        verbose_name = _('观看记录')
        verbose_name_plural = _('观看记录')
        # 添加复合索引
        indexes = [
            # 用户观看历史查询
            models.Index(fields=['user', '-view_date'], name='view_user_idx'),
            # 视频观看统计查询
            models.Index(fields=['video', '-view_date'], name='view_video_idx'),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else self.ip_address
        return f"{user_str} viewed {self.video.title}"


class VideoCollection(models.Model):
    """视频收藏模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_collections')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='collections')
    created_at = models.DateTimeField(_('收藏时间'), auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'video')
        verbose_name = _('视频收藏')
        verbose_name_plural = _('视频收藏')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} collected {self.video.title}"


class Danmaku(models.Model):
    """弹幕模型
    
    TODO: 实现弹幕功能
    - 弹幕发送
    - 弹幕过滤（敏感词）
    - 弹幕举报
    """
    MODE_CHOICES = (
        (0, '滚动'),
        (1, '顶部'),
        (2, '底部'),
    )
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='danmakus', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='danmakus', null=True, blank=True)
    text = models.CharField(_('弹幕内容'), max_length=100)
    time = models.FloatField(_('出现时间(秒)'), default=0, db_index=True)
    mode = models.IntegerField(_('弹幕模式'), choices=MODE_CHOICES, default=0)
    color = models.CharField(_('弹幕颜色'), max_length=10, default='#FFFFFF')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('弹幕')
        verbose_name_plural = _('弹幕')
        ordering = ['time']
        indexes = [
            models.Index(fields=['video', 'time'], name='danmaku_video_time_idx'),
        ]
    
    def __str__(self):
        return f"{self.text[:20]} @ {self.time}s"
