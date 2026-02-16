from rest_framework import serializers
from .models import ModerationResult, FrameRecognition, VideoSummary
import logging

logger = logging.getLogger(__name__)


class ModerationResultSerializer(serializers.ModelSerializer):
    """内容审核结果序列化器（详情）"""
    video = serializers.SerializerMethodField()
    flagged_frames = serializers.SerializerMethodField()
    
    class Meta:
        model = ModerationResult
        fields = [
            'id', 'video', 'status', 'result', 'confidence',
            'neutral_score', 'low_score', 'medium_score', 'high_score',
            'flagged_frames', 'details', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_video(self, obj):
        """获取完整视频信息"""
        if not obj.video:
            logger.warning(f"审核记录 {obj.id} 没有关联的视频")
            return None
        
        request = self.context.get('request')
        video_data = {
            'id': obj.video.id,
            'title': obj.video.title,
            'thumbnail': request.build_absolute_uri(obj.video.thumbnail.url) if request and obj.video.thumbnail else None,
            'user': {
                'id': obj.video.user.id,
                'username': obj.video.user.username,
                'avatar': request.build_absolute_uri(obj.video.user.avatar.url) if request and obj.video.user.avatar else None
            } if obj.video.user else None,
            'created_at': obj.video.created_at
        }
        logger.info(f"序列化视频信息: video_id={obj.video.id}, title={obj.video.title}, user={obj.video.user.username if obj.video.user else None}")
        return video_data
    
    def get_flagged_frames(self, obj):
        """获取问题帧列表，转换图片路径为完整 URL"""
        frames = obj.flagged_frames or []
        request = self.context.get('request')
        
        result = []
        for frame in frames:
            frame_data = frame.copy()
            
            # 转换 image_path 为 image_url
            if 'image_path' in frame_data and request:
                from django.conf import settings
                image_path = frame_data.pop('image_path')
                # 构建完整的媒体 URL
                media_url = f"{settings.MEDIA_URL}ai_moderation/flagged_frames/{obj.video_id}/{image_path}"
                frame_data['image_url'] = request.build_absolute_uri(media_url)
            
            # 添加 reason 字段（如果没有）
            if 'reason' not in frame_data:
                level = frame_data.get('level', 'unknown')
                confidence = frame_data.get('confidence', 0)
                frame_data['reason'] = f'检测到 {level} 级别风险内容（置信度: {confidence:.2%}）'
            
            result.append(frame_data)
        
        return result


class ModerationListSerializer(serializers.ModelSerializer):
    """审核列表序列化器（简化版）"""
    video = serializers.SerializerMethodField()
    flagged_frames = serializers.SerializerMethodField()
    
    class Meta:
        model = ModerationResult
        fields = [
            'id', 'video', 'status', 'result', 'confidence',
            'neutral_score', 'low_score', 'medium_score', 'high_score',
            'flagged_frames', 'error_message', 'created_at', 'updated_at'
        ]
    
    def get_video(self, obj):
        """获取视频信息"""
        if not obj.video:
            return None
        
        request = self.context.get('request')
        return {
            'id': obj.video.id,
            'title': obj.video.title,
            'thumbnail': request.build_absolute_uri(obj.video.thumbnail.url) if request and obj.video.thumbnail else None,
            'user': {
                'id': obj.video.user.id,
                'username': obj.video.user.username
            } if obj.video.user else None,
            'created_at': obj.video.created_at
        }
    
    def get_flagged_frames(self, obj):
        """返回问题帧列表（列表视图只需要数量，但保持数据结构一致）"""
        return obj.flagged_frames or []


class ModerationStatsSerializer(serializers.Serializer):
    """审核统计序列化器"""
    pending = serializers.IntegerField()
    processing = serializers.IntegerField()
    safe = serializers.IntegerField()
    unsafe = serializers.IntegerField()
    uncertain = serializers.IntegerField()
    total = serializers.IntegerField()


class FrameRecognitionSerializer(serializers.Serializer):
    """画面识别请求序列化器"""
    video_id = serializers.IntegerField()
    timestamp = serializers.FloatField()
    frame_data = serializers.CharField(required=False)  # Base64 编码的图片


class FrameRecognitionResultSerializer(serializers.Serializer):
    """画面识别结果序列化器"""
    detected_objects = serializers.ListField()
    scene = serializers.CharField()
    text = serializers.CharField(required=False)
    faces = serializers.ListField()
    confidence = serializers.FloatField()


class VideoSummarySerializer(serializers.Serializer):
    """视频摘要结果序列化器"""
    video_id = serializers.IntegerField()
    summary = serializers.CharField()
    key_frames = serializers.ListField()
    tags = serializers.ListField()
    duration = serializers.FloatField()

