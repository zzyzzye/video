from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from videos.models import Comment, Video
from rest_framework import serializers

class UserCommentVideoSerializer(serializers.ModelSerializer):
    """简化的视频信息序列化器，用于评论列表"""
    cover = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = ('id', 'title', 'cover')
    
    def get_cover(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None

class UserCommentSerializer(serializers.ModelSerializer):
    """用户评论序列化器，包含视频信息"""
    video = UserCommentVideoSerializer(read_only=True)
    likes_count = serializers.IntegerField(default=0, read_only=True)
    replies_count = serializers.SerializerMethodField()
    content = serializers.CharField(source='text')
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Comment
        fields = ('id', 'content', 'video', 'created_at', 'likes_count', 'replies_count')
    
    def get_replies_count(self, obj):
        return obj.replies.count()

class UserCommentViewSet(viewsets.ModelViewSet):
    """
    用户评论管理API
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserCommentSerializer
    
    def get_queryset(self):
        """获取当前用户的所有评论"""
        return Comment.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """创建评论时自动关联当前用户"""
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """删除评论，确保只能删除自己的评论"""
        comment = self.get_object()
        if comment.user != request.user:
            return Response(
                {"detail": "您没有权限删除此评论"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs) 