from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from videos.models import Video

User = get_user_model()


class StatisticsViewSet(viewsets.ViewSet):
    """统计数据视图集"""
    permission_classes = [IsAuthenticated]

    def _check_admin_permission(self, request):
        """检查管理员权限"""
        if not request.user.is_admin:
            return Response(
                {"detail": "权限不足，只有管理员可以查看"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        """获取概览统计数据"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        today = timezone.now().date()
        
        # 用户统计
        all_users = User.objects.filter(role__in=['user', 'vip'])
        total_users = all_users.count()
        vip_users = all_users.filter(is_vip=True).count()
        active_users = all_users.filter(is_active=True).count()
        new_users_today = all_users.filter(created_at__date=today).count()
        
        # 视频统计
        all_videos = Video.objects.filter(deleted_at__isnull=True)
        total_videos = all_videos.count()
        new_videos_today = all_videos.filter(created_at__date=today).count()
        
        # 观看统计
        total_views = all_videos.aggregate(total=Sum('views'))['total'] or 0
        views_today = all_videos.filter(
            created_at__date=today
        ).aggregate(total=Sum('views'))['total'] or 0

        return Response({
            'total_users': total_users,
            'vip_users': vip_users,
            'active_users': active_users,
            'new_users_today': new_users_today,
            'total_videos': total_videos,
            'new_videos_today': new_videos_today,
            'total_views': total_views,
            'views_today': views_today
        })

    @action(detail=False, methods=['get'], url_path='user-trend')
    def user_trend(self, request):
        """获取用户增长趋势"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        dates = []
        counts = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            count = User.objects.filter(
                role__in=['user', 'vip'],
                created_at__date=date
            ).count()
            dates.append(date.strftime('%m-%d'))
            counts.append(count)
        
        return Response({
            'dates': dates,
            'counts': counts
        })

    @action(detail=False, methods=['get'], url_path='video-trend')
    def video_trend(self, request):
        """获取视频上传趋势"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        dates = []
        counts = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            count = Video.objects.filter(
                deleted_at__isnull=True,
                created_at__date=date
            ).count()
            dates.append(date.strftime('%m-%d'))
            counts.append(count)
        
        return Response({
            'dates': dates,
            'counts': counts
        })

    @action(detail=False, methods=['get'], url_path='role-distribution')
    def role_distribution(self, request):
        """获取用户角色分布"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        role_stats = User.objects.filter(
            role__in=['user', 'vip']
        ).values('role').annotate(
            count=Count('id')
        )
        
        role_display_map = {
            'user': '普通用户',
            'vip': 'VIP用户'
        }
        
        result = []
        for stat in role_stats:
            result.append({
                'role': stat['role'],
                'role_display': role_display_map.get(stat['role'], stat['role']),
                'count': stat['count']
            })
        
        return Response(result)

    @action(detail=False, methods=['get'], url_path='status-distribution')
    def status_distribution(self, request):
        """获取视频状态分布"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        status_stats = Video.objects.filter(
            deleted_at__isnull=True
        ).values('status').annotate(
            count=Count('id')
        )
        
        status_display_map = {
            'draft': '草稿',
            'pending': '待审核',
            'approved': '已通过',
            'rejected': '已拒绝',
            'processing': '处理中'
        }
        
        result = []
        for stat in status_stats:
            result.append({
                'status': stat['status'],
                'status_display': status_display_map.get(stat['status'], stat['status']),
                'count': stat['count']
            })
        
        return Response(result)

    @action(detail=False, methods=['get'], url_path='top-videos')
    def top_videos(self, request):
        """获取热门视频排行"""
        error_response = self._check_admin_permission(request)
        if error_response:
            return error_response

        limit = int(request.query_params.get('limit', 10))
        
        videos = Video.objects.filter(
            deleted_at__isnull=True,
            status='approved'
        ).select_related('user').order_by('-views')[:limit]
        
        result = []
        for video in videos:
            result.append({
                'id': video.id,
                'title': video.title,
                'user_username': video.user.username,
                'views': video.views,
                'likes': video.likes,
                'created_at': video.created_at.isoformat()
            })
        
        return Response({
            'results': result
        })
