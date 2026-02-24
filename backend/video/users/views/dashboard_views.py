from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from ..models import Subscription
from videos.models import Video, VideoLike, VideoView


import logging
logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    """仪表盘视图集，提供用户统计数据和相关信息"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """获取创作者仪表盘统计数据"""
        user = request.user
        
        video_count = Video.objects.filter(user=user, deleted_at__isnull=True).count()
        
        like_count = VideoLike.objects.filter(video__user=user, video__deleted_at__isnull=True).count()
        
        follower_count = Subscription.objects.filter(target=user).count()
        
        view_count = Video.objects.filter(user=user, deleted_at__isnull=True).aggregate(total_views=Sum('views_count'))['total_views'] or 0
        
        recent_videos = Video.objects.filter(user=user, deleted_at__isnull=True).order_by('-created_at')[:6]
        
        recent_videos_data = []
        for video in recent_videos:
            # 打印视频时长原始值
            logger.debug(f"视频 {video.id} ({video.title}) 的原始时长: {video.duration}秒")
            
            # 格式化视频时长（假设duration是秒）
            if video.duration and video.duration > 0:
                minutes = int(video.duration // 60)
                seconds = int(video.duration % 60)
                duration = f"{minutes:02d}:{seconds:02d}"
            else:
                duration = "00:00"  # 默认值
                logger.warning(f"视频 {video.id} 的时长为空或为0")
                        
            # 格式化发布时间
            if video.published_at:
                # 计算发布至今的天数
                days_since_publish = (timezone.now() - video.published_at).days
                if days_since_publish < 1:
                    publish_time = "今天"
                elif days_since_publish < 7:
                    publish_time = f"{days_since_publish}天前"
                elif days_since_publish < 30:
                    weeks = days_since_publish // 7
                    publish_time = f"{weeks}周前"
                else:
                    months = days_since_publish // 30
                    publish_time = f"{months}个月前"
            else:
                publish_time = "未发布"
            
            # 构建视频数据
            video_data = {
                'id': video.id,
                'title': video.title,
                'thumbnail': request.build_absolute_uri(video.thumbnail.url) if video.thumbnail else None,
                'duration': duration,
                'views': str(video.views_count),
                'publishTime': publish_time,
                'status': video.status,
                'is_published': video.is_published
            }
            recent_videos_data.append(video_data)
        
        return Response({
            'stats': {
                'videoCount': video_count,
                'likeCount': like_count,
                'followerCount': follower_count,
                'viewCount': view_count
            },
            'recentVideos': recent_videos_data
        })
    
    @action(detail=False, methods=['get'], url_path='chart-data')
    def chart_data(self, request):
        """获取图表数据"""
        user = request.user
        days = int(request.query_params.get('days', 7))  # 默认7天
        
        logger.info(f"获取图表数据 - 用户: {user.username} (ID: {user.id}), 天数: {days}")
        
        # 计算日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # 生成日期列表
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        # 获取每日播放量、点赞数、评论数
        views_data = []
        likes_data = []
        comments_data = []
        
        for date in date_list:
            from datetime import datetime
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            date_start = timezone.make_aware(date_start)
            date_end = timezone.make_aware(date_end)
            
            # 播放量：统计该天的观看记录数
            daily_views = VideoView.objects.filter(
                video__user=user,
                view_date__gte=date_start,
                view_date__lte=date_end
            ).count()
            
            # 点赞数：统计该天新增的点赞数
            daily_likes = VideoLike.objects.filter(
                video__user=user,
                created_at__gte=date_start,
                created_at__lte=date_end
            ).count()
            
            # 评论数：统计该天新增的评论数
            from videos.models import Comment
            daily_comments = Comment.objects.filter(
                video__user=user,
                created_at__gte=date_start,
                created_at__lte=date_end
            ).count()
            
            views_data.append(daily_views)
            likes_data.append(daily_likes)
            comments_data.append(daily_comments)
        
        logger.info(f"每日观看记录: {views_data}")
        logger.info(f"每日新增点赞: {likes_data}")
        logger.info(f"每日新增评论: {comments_data}")
        
        # 格式化日期
        formatted_dates = [date.strftime('%m-%d') for date in date_list]
        
        # 视频状态分布（排除已删除）
        status_distribution = Video.objects.filter(user=user, deleted_at__isnull=True).values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        status_data = [
            {'status': item['status'], 'count': item['count']}
            for item in status_distribution
        ]
        
        # 视频分类分布（排除已删除）
        category_distribution = Video.objects.filter(user=user, deleted_at__isnull=True).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # 只取前10个分类
        
        category_data = [
            {'category': item['category__name'] or '未分类', 'count': item['count']}
            for item in category_distribution
        ]
        
        # 视频时长分布（按区间统计，排除已删除）
        duration_ranges = [
            (0, 60, '1分钟内'),
            (60, 300, '1-5分钟'),
            (300, 600, '5-10分钟'),
            (600, 1800, '10-30分钟'),
            (1800, 3600, '30-60分钟'),
            (3600, float('inf'), '1小时以上'),
        ]
        
        duration_data = []
        for min_duration, max_duration, label in duration_ranges:
            if max_duration == float('inf'):
                count = Video.objects.filter(
                    user=user,
                    deleted_at__isnull=True,
                    duration__gte=min_duration
                ).count()
            else:
                count = Video.objects.filter(
                    user=user,
                    deleted_at__isnull=True,
                    duration__gte=min_duration,
                    duration__lt=max_duration
                ).count()
            
            if count > 0:  # 只添加有数据的区间
                duration_data.append({
                    'range': label,
                    'count': count
                })
        
        return Response({
            'trend': {
                'dates': formatted_dates,
                'views': views_data,
                'likes': likes_data,
                'comments': comments_data
            },
            'categoryDistribution': category_data,
            'durationDistribution': duration_data
        }) 