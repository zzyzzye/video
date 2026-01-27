from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import UserNotification, NotificationSetting
from ..serializers import UserNotificationSerializer, NotificationSettingSerializer

class UserNotificationViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """
    用户消息通知API
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return UserNotification.objects.filter(user=user)
    
    def list(self, request, *args, **kwargs):
        """获取消息列表，支持按类型筛选"""
        notification_type = request.query_params.get('type')
        queryset = self.get_queryset()
        
        if notification_type and notification_type != 'all':
            queryset = queryset.filter(type=notification_type)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记单个消息为已读"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({"status": "success"})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有消息为已读"""
        queryset = self.get_queryset().filter(read=False)
        queryset.update(read=True)
        return Response({"status": "success", "count": queryset.count()})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """清空所有消息"""
        count = self.get_queryset().count()
        self.get_queryset().delete()
        return Response({"status": "success", "count": count})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读消息数量"""
        count = self.get_queryset().filter(read=False).count()
        return Response({"count": count})


class NotificationSettingViewSet(viewsets.ModelViewSet):
    """
    用户通知设置视图集
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户的通知设置"""
        return NotificationSetting.objects.filter(user=self.request.user)
    
    def list(self, request):
        """获取当前用户的通知设置"""
        try:
            setting = NotificationSetting.objects.get(user=request.user)
            serializer = self.get_serializer(setting)
            return Response(serializer.data)
        except NotificationSetting.DoesNotExist:
            # 如果不存在，创建默认设置
            setting = NotificationSetting.objects.create(user=request.user)
            serializer = self.get_serializer(setting)
            return Response(serializer.data)
    
    def create(self, request):
        """创建或更新通知设置"""
        try:
            setting = NotificationSetting.objects.get(user=request.user)
            serializer = self.get_serializer(setting, data=request.data, partial=True)
        except NotificationSetting.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """更新通知设置"""
        setting = self.get_object()
        serializer = self.get_serializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def get_serializer_class(self):
        """获取序列化器类"""
        from ..serializers import NotificationSettingSerializer
        return NotificationSettingSerializer 