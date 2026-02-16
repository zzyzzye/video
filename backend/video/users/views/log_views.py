from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from core.permissions import IsSuperAdmin
from users.models_logs import SystemOperationLog
from users.serializers import SystemOperationLogSerializer


class SystemOperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """系统操作日志视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = SystemOperationLogSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = SystemOperationLog.objects.all()
        
        # 搜索
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(operator_username__icontains=search) |
                Q(action__icontains=search) |
                Q(description__icontains=search) |
                Q(target_name__icontains=search)
            )
        
        # 日志类型筛选
        log_type = self.request.query_params.get('log_type', '')
        if log_type:
            queryset = queryset.filter(log_type=log_type)
        
        # 日志级别筛选
        level = self.request.query_params.get('level', '')
        if level:
            queryset = queryset.filter(level=level)
        
        # 操作者筛选
        operator = self.request.query_params.get('operator', '')
        if operator:
            queryset = queryset.filter(operator_username__icontains=operator)
        
        # 时间范围筛选
        start_date = self.request.query_params.get('start_date', '')
        end_date = self.request.query_params.get('end_date', '')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取日志统计信息"""
        now = timezone.now()
        
        # 今日日志数
        today_count = SystemOperationLog.objects.filter(
            created_at__gte=now.replace(hour=0, minute=0, second=0)
        ).count()
        
        # 本周日志数
        week_start = now - timedelta(days=now.weekday())
        week_count = SystemOperationLog.objects.filter(
            created_at__gte=week_start.replace(hour=0, minute=0, second=0)
        ).count()
        
        # 本月日志数
        month_start = now.replace(day=1, hour=0, minute=0, second=0)
        month_count = SystemOperationLog.objects.filter(
            created_at__gte=month_start
        ).count()
        
        # 按类型统计
        type_stats = SystemOperationLog.objects.values('log_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 按级别统计
        level_stats = SystemOperationLog.objects.values('level').annotate(
            count=Count('id')
        )
        
        # 最活跃操作者
        operator_stats = SystemOperationLog.objects.values('operator_username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'today_count': today_count,
            'week_count': week_count,
            'month_count': month_count,
            'type_stats': list(type_stats),
            'level_stats': list(level_stats),
            'operator_stats': list(operator_stats)
        })
    
    @action(detail=False, methods=['post'])
    def clear_old_logs(self, request):
        """清理旧日志"""
        days = request.data.get('days', 90)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = SystemOperationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        return Response({
            'message': f'已清理 {deleted_count} 条日志',
            'deleted_count': deleted_count
        })
