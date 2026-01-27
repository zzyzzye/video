from rest_framework import serializers


class ModerationResultSerializer(serializers.Serializer):
    """内容审核结果序列化器"""
    video_id = serializers.IntegerField()
    is_safe = serializers.BooleanField()
    confidence = serializers.FloatField()
    categories = serializers.DictField()
    flagged_frames = serializers.ListField()
    message = serializers.CharField()


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
