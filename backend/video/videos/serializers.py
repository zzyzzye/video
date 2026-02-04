from rest_framework import serializers
from .models import Category, Tag, Video, VideoLike, Comment, VideoView, VideoCollection
from django.contrib.auth import get_user_model

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at')


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'created_at')


class UserBriefSerializer(serializers.ModelSerializer):
    """用户简略信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar')


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    user = UserBriefSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'video', 'parent', 'text', 'is_active', 
                  'created_at', 'updated_at', 'replies_count')
        read_only_fields = ('id', 'user', 'is_active', 'created_at', 'updated_at')
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommentDetailSerializer(CommentSerializer):
    """评论详细信息序列化器，包含回复"""
    replies = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ('replies',)
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_active=True)
        return CommentSerializer(replies, many=True).data


class VideoSerializer(serializers.ModelSerializer):
    """视频序列化器"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    user = UserBriefSerializer(read_only=True)
    reviewer = UserBriefSerializer(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    days_until_permanent_delete = serializers.SerializerMethodField()
    resolution_label = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'description', 'category', 'tags', 'user',
                  'thumbnail', 'views_count', 'likes_count', 'comments_count',
                  'status', 'is_published', 'created_at', 'published_at',
                  'duration', 'video_file', 'hls_file', 'review_remark', 'reviewer', 'reviewed_at',
                  'deleted_at', 'is_deleted', 'days_until_permanent_delete',
                  'resolution', 'resolution_label',
                  # 视频技术参数
                  'width', 'height', 'aspect_ratio', 'video_codec', 'audio_codec',
                  'bitrate', 'video_bitrate', 'audio_bitrate', 'frame_rate', 
                  'file_size', 'file_size_display',
                  # 字幕信息
                  'has_subtitle', 'subtitle_type', 'subtitle_language',
                  # 发布设置
                  'view_permission', 'comment_permission', 'allow_download', 
                  'enable_danmaku', 'show_in_profile', 'scheduled_publish_time', 
                  'original_type')
        read_only_fields = ('id', 'user', 'views_count', 'likes_count', 
                           'comments_count', 'status', 'created_at', 'reviewer', 'reviewed_at',
                           'deleted_at', 'is_deleted', 
                           'has_subtitle', 'subtitle_type', 'subtitle_language')
    
    def get_days_until_permanent_delete(self, obj):
        """计算距离永久删除还有多少天"""
        if not obj.deleted_at:
            return None
        from datetime import timedelta
        from django.utils import timezone
        thirty_days_later = obj.deleted_at + timedelta(days=30)
        days_left = (thirty_days_later - timezone.now()).days
        return max(0, days_left)
    
    def get_resolution_label(self, obj):
        """返回分辨率标签：4K, 2K 或 None"""
        if obj.resolution >= 2160:
            return '4K'
        elif obj.resolution >= 1440:
            return '2K'
        return None
    
    def get_file_size_display(self, obj):
        """返回人类可读的文件大小"""
        if not obj.file_size:
            return None
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class VideoCreateSerializer(serializers.ModelSerializer):
    """视频创建序列化器"""
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    new_tags = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False
    )
    title = serializers.CharField(max_length=100, required=False, default="未命名视频")
    
    class Meta:
        model = Video
        fields = ('title', 'description', 'category_id', 'tag_ids', 'new_tags', 
                  'video_file', 'thumbnail',
                  # 发布设置
                  'view_permission', 'comment_permission', 'allow_download', 
                  'enable_danmaku', 'show_in_profile', 'scheduled_publish_time', 
                  'original_type')
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        new_tags = validated_data.pop('new_tags', [])
        category_id = validated_data.pop('category_id', None)
        
        # 确保有标题，如果没有则使用默认标题
        if 'title' not in validated_data or not validated_data['title']:
            validated_data['title'] = "未命名视频"
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                validated_data['category'] = category
            except Category.DoesNotExist:
                pass
        
        validated_data['user'] = self.context['request'].user
        video = Video.objects.create(**validated_data)
        
        # 添加已有标签
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            video.tags.set(tags)
        
        # 创建并添加新标签
        if new_tags:
            for tag_name in new_tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                video.tags.add(tag)
        
        return video
        
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        new_tags = validated_data.pop('new_tags', None)
        category_id = validated_data.pop('category_id', None)
        
        # 更新分类
        if category_id:
            try:
                instance.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                instance.category = None
        elif category_id == None and 'category_id' in self.initial_data:
            instance.category = None
            
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 保存实例
        instance.save()
        
        # 更新标签
        if tag_ids is not None:
            existing_tags = Tag.objects.filter(id__in=tag_ids)
            # 如果同时提供了new_tags，先只设置现有标签
            if new_tags:
                instance.tags.set(existing_tags)
                # 然后添加新标签
                for tag_name in new_tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    instance.tags.add(tag)
            else:
                # 只有现有标签，直接设置
                instance.tags.set(existing_tags)
        
        return instance


class VideoDetailSerializer(VideoSerializer):
    """视频详细信息序列化器"""
    hls_file = serializers.SerializerMethodField()
    duration = serializers.FloatField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
    reviewer = UserBriefSerializer(read_only=True)
    
    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ('hls_file', 'duration', 'is_liked', 'is_collected', 
                                               'reviewer', 'reviewed_at', 'review_remark')
    
    def get_hls_file(self, obj):
        """返回标准化的HLS文件路径（使用正斜杠）"""
        if obj.hls_file:
            # 将Windows路径分隔符转换为URL路径分隔符
            return obj.hls_file.replace('\\', '/')
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VideoLike.objects.filter(user=request.user, video=obj).exists()
        return False
    
    def get_is_collected(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import VideoCollection
            return VideoCollection.objects.filter(user=request.user, video=obj).exists()
        return False


class VideoLikeSerializer(serializers.ModelSerializer):
    """视频点赞序列化器"""
    user = UserBriefSerializer(read_only=True)
    video = VideoSerializer(read_only=True)
    
    class Meta:
        model = VideoLike
        fields = ('id', 'user', 'video', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class VideoViewSerializer(serializers.ModelSerializer):
    """视频观看记录序列化器"""
    video = VideoSerializer(read_only=True)
    
    class Meta:
        model = VideoView
        fields = ('id', 'video', 'watched_duration', 'view_date')
        read_only_fields = ('id', 'view_date')


class VideoCollectionSerializer(serializers.ModelSerializer):
    """视频收藏序列化器"""
    video = VideoSerializer(read_only=True)
    
    class Meta:
        model = VideoCollection
        fields = ('id', 'video', 'created_at')
        read_only_fields = ('id', 'created_at') 
 


class DanmakuSerializer(serializers.ModelSerializer):
    """弹幕序列化器
    
    TODO: 添加敏感词过滤
    """
    class Meta:
        model = None  # TODO: 迁移后改为 Danmaku
        fields = ('id', 'video', 'text', 'time', 'mode', 'color', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        # TODO: 实现弹幕创建逻辑
        pass
