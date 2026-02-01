from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import F, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
import shutil
from .models import Category, Tag, Video, VideoLike, Comment, VideoView, VideoCollection
from .serializers import (
    CategorySerializer,
    TagSerializer,
    VideoSerializer,
    VideoCreateSerializer,
    VideoDetailSerializer,
    CommentSerializer,
    CommentDetailSerializer,
    VideoLikeSerializer,
    VideoViewSerializer,
    VideoCollectionSerializer
)
from .pagination import (
    VideoListPagination,
    CommentListPagination,
    HistoryListPagination,
    CollectionListPagination
)
from .tasks import process_video
import logging
from rest_framework.views import APIView
from rest_framework import serializers
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def check_video_view_permission(video, user):
    """检查用户是否有权限观看视频
    
    Args:
        video: Video 实例
        user: User 实例
    
    Returns:
        tuple: (has_permission: bool, error_message: str)
    """
    # 视频所有者始终可以观看
    if user.is_authenticated and video.user == user:
        return True, None
    
    # 管理员始终可以观看
    if user.is_authenticated and user.is_staff:
        return True, None
    
    # 检查观看权限
    if video.view_permission == 'public':
        return True, None
    elif video.view_permission == 'private':
        return False, '该视频为私密视频，仅作者可见'
    elif video.view_permission == 'fans':
        if not user.is_authenticated:
            return False, '该视频仅粉丝可见，请先登录'
        return True, None
    
    return False, '无权观看该视频'


def check_comment_permission(video, user):
    """检查用户是否有权限评论视频
    
    Args:
        video: Video 实例
        user: User 实例
    
    Returns:
        tuple: (has_permission: bool, error_message: str)
    """
    # 未登录用户不能评论
    if not user.is_authenticated:
        return False, '请先登录后再评论'
    
    # 检查评论权限
    if video.comment_permission == 'none':
        return False, '该视频已关闭评论'
    elif video.comment_permission == 'all':
        return True, None
    elif video.comment_permission == 'fans':
        # 视频所有者始终可以评论
        if video.user == user:
            return True, None
        # TODO: 实现粉丝关系检查
        # 暂时允许所有登录用户评论
        # is_fan = user in video.user.followers.all()
        # if not is_fan:
        #     return False, '该视频仅粉丝可评论'
        return True, None
    
    return False, '无权评论该视频'


class CategoryViewSet(viewsets.ModelViewSet):
    """分类视图集"""
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class TagViewSet(viewsets.ModelViewSet):
    """标签视图集"""
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class VideoViewSet(viewsets.ModelViewSet):
    """视频视图集"""
    queryset = Video.objects.filter(is_published=True, status='approved')
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'user__username']
    ordering_fields = ['created_at', 'views_count', 'likes_count', 'comments_count']
    ordering = ['-created_at']
    pagination_class = VideoListPagination  # 使用自定义分页
    
    def get_queryset(self):
        queryset = Video.objects.all()
        
        # 对于恢复和永久删除操作，需要包含已删除的视频
        if self.action in ['restore', 'permanent_delete', 'recycle_bin']:
            # 不过滤已删除的视频
            pass
        else:
            # 其他操作排除已软删除的视频
            queryset = queryset.filter(deleted_at__isnull=True)
        
        # 优化：预加载关联对象，避免N+1查询
        queryset = queryset.select_related('user', 'category', 'reviewer')
        queryset = queryset.prefetch_related('tags')
        
        # 如果是已认证用户，可以查看自己的所有视频（包括未发布的）
        if self.request.user.is_authenticated:
            if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'publish', 'upload_thumbnail',
             'detect_subtitle', 'restore', 'permanent_delete', 'trigger_transcode_action']:
                # 个人可以访问自己的所有视频
                return queryset.filter(
                    Q(user=self.request.user) | 
                    Q(is_published=True, status='approved')
                )
        
        # 否则只能查看已发布且审核通过的视频
        queryset = queryset.filter(is_published=True, status='approved')
        
        # 按分类筛选
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 按标签筛选
        tag_id = self.request.query_params.get('tag_id')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # 按用户筛选（支持 user_id 和 user 两种参数名）
        user_id = self.request.query_params.get('user_id') or self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return VideoCreateSerializer
        elif self.action == 'retrieve':
            return VideoDetailSerializer
        return VideoSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'publish', 'restore', 'permanent_delete']:
            # 只有视频所有者才能修改、删除、发布和恢复视频
            return [permissions.IsAuthenticated()]
        elif self.action == 'recycle_bin':
            # 回收站需要登录
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def perform_destroy(self, instance):
        """软删除视频（不删除文件）"""
        instance.soft_delete()
        logger.info(f"视频 {instance.id} ({instance.title}) 已软删除，将在 30 天后永久删除")
    
    def retrieve(self, request, *args, **kwargs):
        """获取视频详情，添加权限验证"""
        instance = self.get_object()
        
        # 检查观看权限
        has_permission, error_message = check_video_view_permission(instance, request.user)
        if not has_permission:
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """手动触发视频转码处理"""
        from .tasks import process_video, is_video_locked
        
        video = self.get_object()
        
        # 检查权限（管理员或视频所有者）
        if not (request.user.is_staff or video.user == request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查视频文件是否存在
        if not video.video_file:
            return Response(
                {"detail": "视频文件不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否已经有任务在处理
        if is_video_locked(video.id):
            return Response({
                "detail": "视频正在处理中，请稍后再试",
                "video_id": video.id
            }, status=status.HTTP_202_ACCEPTED)
        
        # 触发转码任务
        try:
            process_video.delay(video.id)
            logger.info(f"手动触发视频 {video.id} 的转码任务")
            return Response({
                "detail": "转码任务已提交",
                "video_id": video.id
            })
        except Exception as e:
            logger.error(f"触发转码任务失败: {str(e)}")
            return Response(
                {"detail": f"触发转码任务失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """恢复已删除的视频"""
        video = self.get_object()
        
        # 检查权限
        if video.user != request.user:
            return Response(
                {"detail": "无权恢复此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not video.is_deleted:
            return Response(
                {"detail": "视频未被删除"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video.restore()
        logger.info(f"视频 {video.id} ({video.title}) 已恢复")
        
        serializer = self.get_serializer(video)
        return Response({
            "detail": "视频已恢复",
            "video": serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recycle_bin(self, request):
        """获取回收站中的视频列表（仅当前用户）"""
        queryset = Video.objects.filter(
            user=request.user,
            deleted_at__isnull=False
        ).select_related('user', 'category').prefetch_related('tags').order_by('-deleted_at')
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='permanent-delete')
    def permanent_delete(self, request, pk=None):
        """永久删除视频（立即删除文件和数据库记录）"""
        video = self.get_object()
        
        # 检查权限
        if video.user != request.user:
            return Response(
                {"detail": "无权删除此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not video.is_deleted:
            return Response(
                {"detail": "请先将视频移至回收站"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_id = video.id
        video_title = video.title
        
        # 删除文件
        try:
            # 删除原始视频文件
            if video.video_file:
                video_file_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)
                if os.path.exists(video_file_path):
                    os.remove(video_file_path)
                    logger.info(f"已删除视频文件: {video_file_path}")
            
            # 删除 HLS 文件目录
            if video.hls_file:
                hls_path_parts = video.hls_file.split('/')
                if len(hls_path_parts) >= 3:
                    hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', hls_path_parts[2])
                    if os.path.exists(hls_dir):
                        shutil.rmtree(hls_dir)
                        logger.info(f"已删除 HLS 目录: {hls_dir}")
            
            # 删除缩略图
            if video.thumbnail:
                thumbnail_path = os.path.join(settings.MEDIA_ROOT, video.thumbnail.name)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                    logger.info(f"已删除缩略图: {thumbnail_path}")
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
        
        # 永久删除数据库记录
        video.delete()
        logger.info(f"视频 {video_id} ({video_title}) 已永久删除")
        
        return Response(
            {"detail": "视频已永久删除"},
            status=status.HTTP_200_OK
        )
    
    def perform_create(self, serializer):
        video = serializer.save(user=self.request.user)
        # 不在这里立即触发处理任务，等待用户上传封面后再处理
        # 或者在发布视频时触发处理
        logger.info(f"视频创建成功，ID: {video.id}，等待用户上传封面")
        
    def create(self, request, *args, **kwargs):
        from django.db import transaction
        
        # 记录请求内容
        logger.info(f"接收到视频上传请求 FILES: {request.FILES}")
        logger.info(f"请求数据: {request.data}")
        
        # 检查是否提供了视频文件
        if 'video_file' not in request.FILES:
            logger.error("没有提供视频文件")
            return Response(
                {"detail": "没有提供视频文件", "field": "video_file"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_file = request.FILES['video_file']
        video = None
        
        try:
            # 注意：Django 的 FileField 在 save() 时会立即保存文件到磁盘
            # 即使在 transaction.atomic() 内部，文件操作也不受事务控制
            # 所以我们需要在 except 块中手动清理文件
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                # 保存视频记录（此时文件已经保存到磁盘）
                video = serializer.save(user=request.user)
                
                logger.info(f"视频创建成功，ID: {video.id}，等待用户上传封面")
                
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                
        except Exception as e:
            logger.error(f"视频创建失败: {str(e)}")
            
            # 如果视频对象已创建但事务失败，清理已保存的文件
            if video and video.video_file:
                try:
                    file_path = video.video_file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"已清理失败上传的文件: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"清理上传文件失败: {str(cleanup_error)}")
            
            return Response(
                {"detail": f"视频创建失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞视频"""
        video = self.get_object()
        user = request.user
        
        # 检查是否已经点赞
        like, created = VideoLike.objects.get_or_create(video=video, user=user)
        
        if created:
            # 更新视频点赞数
            video.likes_count = F('likes_count') + 1
            video.save(update_fields=['likes_count'])
            video.refresh_from_db()
            
            return Response(
                {"detail": f"点赞成功", "likes_count": video.likes_count}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"detail": "您已经点赞过该视频", "likes_count": video.likes_count}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """取消点赞视频"""
        video = self.get_object()
        user = request.user
        
        try:
            like = VideoLike.objects.get(video=video, user=user)
            like.delete()
            
            # 更新视频点赞数
            video.likes_count = F('likes_count') - 1
            video.save(update_fields=['likes_count'])
            video.refresh_from_db()
            
            return Response(
                {"detail": "取消点赞成功", "likes_count": video.likes_count}, 
                status=status.HTTP_200_OK
            )
        except VideoLike.DoesNotExist:
            return Response(
                {"detail": "您还没有点赞该视频", "likes_count": video.likes_count}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """记录视频观看"""
        video = self.get_object()
        user = request.user if request.user.is_authenticated else None
        
        # 获取客户端信息
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # 记录观看数据
        watched_duration = request.data.get('watched_duration', 0)
        
        should_count = False  # 是否应该增加播放次数
        
        # 对于已登录用户
        if user:
            # 查找该用户对该视频的观看记录
            existing_view = VideoView.objects.filter(
                video=video,
                user=user
            ).order_by('-view_date').first()
            
            # 如果已有观看记录，更新它
            if existing_view:
                time_diff = timezone.now() - existing_view.view_date
                
                # 如果距离上次观看超过1小时，增加播放次数
                if time_diff.total_seconds() > 3600:  # 1小时 = 3600秒
                    should_count = True
                
                # 更新现有记录
                existing_view.view_date = timezone.now()
                existing_view.watched_duration = watched_duration
                existing_view.ip_address = ip_address
                existing_view.user_agent = user_agent
                existing_view.save()
                
                view = existing_view
                logger.info(f"更新用户 {user.id} 对视频 {video.id} 的观看记录")
            else:
                # 首次观看，创建新记录
                view = VideoView.objects.create(
                    video=video,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    watched_duration=watched_duration
                )
                should_count = True
                logger.info(f"创建用户 {user.id} 对视频 {video.id} 的观看记录")
            
            if should_count:
                video.views_count = F('views_count') + 1
                video.save(update_fields=['views_count'])
                video.refresh_from_db()
        else:
            # 未登录用户，每次都创建新记录并计数
            view = VideoView.objects.create(
                video=video,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
                watched_duration=watched_duration
            )
            
            # 更新视频播放次数
            video.views_count = F('views_count') + 1
            video.save(update_fields=['views_count'])
            video.refresh_from_db()
        
        return Response(
            {"detail": "观看记录已保存", "views_count": video.views_count}, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布视频"""
        from .tasks import is_video_locked
        
        video = self.get_object()
        
        # 确保是视频所有者
        if video.user != request.user:
            return Response(
                {"detail": "您不是该视频的所有者"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 如果视频还未开始处理，触发处理任务
        if video.status == 'uploading':
            # 检查是否已经有任务在处理（通过 Redis 锁）
            if is_video_locked(video.id):
                logger.info(f"视频 {video.id} 已有任务在处理中（Redis锁存在）")
                return Response(
                    {"detail": "视频正在处理中，请稍后再试"}, 
                    status=status.HTTP_202_ACCEPTED
                )
            
            logger.info(f"视频尚未处理，触发处理任务，视频ID: {video.id}")
            # 注意：不在这里改状态，让 task 自己通过原子操作来改
            # 这样可以保证只有一个 task 能成功获取处理权
            process_video.delay(video.id)
            return Response(
                {"detail": "视频正在处理中，处理完成后将自动提交审核"}, 
                status=status.HTTP_202_ACCEPTED
            )
        
        # 如果视频正在处理中
        if video.status == 'processing':
            return Response(
                {"detail": "视频正在处理中，请稍后再试"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 如果视频处理失败
        if video.status == 'failed':
            return Response(
                {"detail": "视频处理失败，无法发布"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 视频处理完成后，提交审核
        if video.status in ['ready', 'pending']:
            # 更新状态为待审核
            video.status = 'pending'
            video.save(update_fields=['status'])
            
            return Response(
                {"detail": "视频已提交审核，请等待管理员审核"}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"detail": f"视频当前状态: {video.get_status_display()}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'],url_path='my_videos')
    def my_videos(self, request):
        """获取我的视频列表，包括未发布的视频"""
        # 优化：预加载关联对象，排除已删除的视频
        videos = Video.objects.filter(
            user=request.user,
            deleted_at__isnull=True  # 排除已软删除的视频
        ).select_related(
            'user', 'category', 'reviewer'
        ).prefetch_related('tags')
        
        # 按状态筛选
        status_param = request.query_params.get('status')
        if status_param:
            videos = videos.filter(status=status_param)
        
        # 按发布状态筛选
        is_published = request.query_params.get('is_published')
        if is_published is not None:
            is_published = is_published.lower() == 'true'
            videos = videos.filter(is_published=is_published)
        
        # 添加排序支持
        ordering = request.query_params.get('ordering')
        if ordering:
            videos = videos.order_by(ordering)
        
        # 添加搜索支持
        search = request.query_params.get('search')
        if search:
            videos = videos.filter(title__icontains=search)
        
        # 使用logger代替print
        logger.debug(f"查询参数: {request.query_params}")
        logger.debug(f"查询结果数量: {videos.count()}")
        
        page = self.paginate_queryset(videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='trigger-transcode')
    def trigger_transcode_action(self, request, pk=None):
        """
        手动触发视频转码
        
        允许状态为 uploading 或 pending_subtitle_edit 的视频触发转码
        只有视频上传者才能触发
        """
        video = self.get_object()
        
        # 确保是视频所有者
        if video.user != request.user:
            return Response(
                {"detail": "您不是该视频的所有者"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查视频状态 - 允许 uploading 状态（表示正在等待处理）
        if video.status not in ['pending_subtitle_edit', 'uploading']:
            logger.warning(f"用户 {request.user.id} 尝试触发视频 {video.id} 转码，但状态为 {video.status}")
            return Response(
                {'error': f'视频状态为 {video.get_status_display()}，无法触发转码'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 如果状态是 uploading，说明还没开始处理，直接触发处理任务
        if video.status == 'uploading':
            logger.info(f"用户 {request.user.id} 触发视频 {video.id} 处理（从 uploading 状态）")
            from .tasks import process_video, is_video_locked
            
            # 检查是否已经有任务在处理
            if is_video_locked(video.id):
                return Response({
                    'message': '视频正在处理中',
                    'video_id': video.id,
                    'status': video.status
                }, status=status.HTTP_202_ACCEPTED)
            
            # 触发处理任务
            process_video.delay(video.id)
            return Response({
                'message': '视频处理已启动',
                'video_id': video.id,
                'status': video.status
            }, status=status.HTTP_202_ACCEPTED)
        
        # 状态是 pending_subtitle_edit，更新为转码中
        video.status = 'transcoding'
        video.save(update_fields=['status'])
        
        logger.info(f"用户 {request.user.id} 触发视频 {video.id} 转码")
        
        # 触发转码任务
        from .tasks import process_video
        process_video.delay(video.id)
        
        return Response({
            'message': '转码已启动',
            'video_id': video.id,
            'status': video.status
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='upload-thumbnail', parser_classes=[MultiPartParser, FormParser])
    def upload_thumbnail(self, request, pk=None):
        """上传视频缩略图"""
        from django.db import transaction

        video = self.get_object()

        # 确保是视频所有者
        if video.user != request.user:
            return Response(
                {"detail": "您不是该视频的所有者"},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'thumbnail' not in request.FILES:
            return Response(
                {"detail": "没有提供缩略图文件"},
                status=status.HTTP_400_BAD_REQUEST
            )

        thumbnail_file = request.FILES['thumbnail']

        # 检查文件类型
        if not thumbnail_file.content_type.startswith('image/'):
            return Response(
                {"detail": "只能上传图片文件"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查文件大小 (2MB)
        if thumbnail_file.size > 2 * 1024 * 1024:
            return Response(
                {"detail": "缩略图文件不能超过2MB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 保存旧缩略图路径，以便回滚
        old_thumbnail = video.thumbnail.name if video.thumbnail else None
        new_thumbnail_path = None

        try:
            with transaction.atomic():
                # 保存缩略图
                video.thumbnail = thumbnail_file
                video.save(update_fields=['thumbnail'])
                new_thumbnail_path = video.thumbnail.path if video.thumbnail else None

                logger.info(f"封面上传成功，视频ID: {video.id}，封面路径: {video.thumbnail.name}")

                # 删除旧缩略图（如果存在且不同）
                if old_thumbnail and old_thumbnail != video.thumbnail.name:
                    old_thumbnail_path = os.path.join(settings.MEDIA_ROOT, old_thumbnail)
                    if os.path.exists(old_thumbnail_path):
                        try:
                            os.remove(old_thumbnail_path)
                            logger.info(f"已删除旧缩略图: {old_thumbnail_path}")
                        except Exception as e:
                            logger.warning(f"删除旧缩略图失败: {str(e)}")

                return Response({
                    "detail": "缩略图上传成功",
                    "thumbnail_url": request.build_absolute_uri(video.thumbnail.url)
                })

        except Exception as e:
            logger.error(f"缩略图上传失败: {str(e)}")

            # 如果新文件已保存但数据库操作失败，删除新文件
            if new_thumbnail_path and os.path.exists(new_thumbnail_path):
                try:
                    os.remove(new_thumbnail_path)
                    logger.info(f"已清理失败上传的缩略图: {new_thumbnail_path}")
                except Exception as cleanup_error:
                    logger.error(f"清理缩略图失败: {str(cleanup_error)}")

            return Response(
                {"detail": f"缩略图上传失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='detect-subtitle')
    def detect_subtitle(self, request, pk=None):
        """检测视频字幕"""
        video = self.get_object()

        # 确保是视频所有者
        if video.user != request.user:
            return Response(
                {"detail": "您不是该视频的所有者"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 检查视频文件是否存在
        if not video.video_file:
            return Response(
                {"detail": "视频文件不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger.info(f"开始检测视频 {video.id} 的字幕")
            from .subtitle_detector import get_subtitle_detector

            # 获取视频文件路径
            video_path = video.video_file.path
            logger.info(f"视频路径: {video_path}")

            # 获取字幕检测器
            logger.info("正在初始化字幕检测器...")
            detector = get_subtitle_detector()
            logger.info("字幕检测器初始化完成")

            # 检测字幕
            logger.info("开始执行字幕检测...")
            result = detector.detect_subtitle(video_path)
            logger.info(f"字幕检测完成，结果: {result}")

            return Response({
                "detail": "字幕检测完成",
                "subtitle_info": result
            })

        except Exception as e:
            logger.error(f"字幕检测失败: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"字幕检测失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get', 'put'], url_path='subtitles')
    def subtitles(self, request, pk=None):
        """外置字幕（JSON）获取/保存

        GET: 返回 JSON 数组
        PUT: 保存 JSON 数组（替换）
        """
        video = self.get_object()

        # 确保是视频所有者或管理员
        if not (request.user.is_staff or video.user == request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.method.lower() == 'get':
            return Response({
                "video_id": video.id,
                "subtitles": video.subtitles_draft or []
            })

        data = request.data
        subtitles = data.get('subtitles', None)
        if subtitles is None:
            return Response(
                {"detail": "缺少 subtitles 字段"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(subtitles, list):
            return Response(
                {"detail": "subtitles 必须为数组"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 基础校验（尽量宽松，避免阻塞编辑；更严格校验可以后续增强）
        for i, item in enumerate(subtitles):
            if not isinstance(item, dict):
                return Response(
                    {"detail": f"subtitles[{i}] 必须为对象"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'startTime' not in item or 'endTime' not in item:
                return Response(
                    {"detail": f"subtitles[{i}] 缺少 startTime/endTime"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        video.subtitles_draft = subtitles
        video.has_subtitle = len(subtitles) > 0
        video.subtitle_type = 'soft' if video.has_subtitle else 'none'
        video.save(update_fields=['subtitles_draft', 'has_subtitle', 'subtitle_type'])

        return Response({
            "detail": "字幕已保存",
            "video_id": video.id,
            "count": len(subtitles)
        })

    @action(detail=True, methods=['get'], url_path='subtitles\.vtt')
    def subtitles_vtt(self, request, pk=None):
        """输出 WebVTT 字幕文件（用于播放器加载）"""
        video = self.get_object()

        # 观看权限：与 retrieve 类似，公开视频可读；作者/管理员可读
        has_permission, error_message = check_video_view_permission(video, request.user)
        if not has_permission:
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )

        subtitles = video.subtitles_draft or []
        lines = ["WEBVTT", ""]

        def _format_vtt_time(seconds):
            try:
                seconds = float(seconds)
            except Exception:
                seconds = 0.0
            if seconds < 0:
                seconds = 0.0
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            ms = int(round((seconds - int(seconds)) * 1000))
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"

        for i, sub in enumerate(subtitles):
            if not isinstance(sub, dict):
                continue
            start = sub.get('startTime', 0)
            end = sub.get('endTime', 0)
            text = (sub.get('text') or '').strip()
            translation = (sub.get('translation') or '').strip()
            if not text and not translation:
                continue

            lines.append(str(i + 1))
            lines.append(f"{_format_vtt_time(start)} --> {_format_vtt_time(end)}")
            if text:
                lines.append(text)
            if translation:
                lines.append(translation)
            lines.append("")

        content = "\n".join(lines)
        return HttpResponse(content, content_type='text/vtt; charset=utf-8')


class CommentViewSet(viewsets.ModelViewSet):
    """评论视图集"""
    queryset = Comment.objects.filter(is_active=True, parent=None)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CommentListPagination  # 使用游标分页
    ordering = ['-created_at']  # 明确指定排序字段，游标分页必需
    
    def get_queryset(self):
        """优化查询：预加载用户信息"""
        queryset = super().get_queryset()
        
        # 优化：预加载用户信息，避免N+1查询
        queryset = queryset.select_related('user', 'video')
        
        # 按视频筛选
        video_id = self.request.query_params.get('video_id')
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        
        # 确保排序
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CommentDetailSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        
        # 更新视频评论数
        video = comment.video
        video.comments_count = F('comments_count') + 1
        video.save(update_fields=['comments_count'])
    
    def create(self, request, *args, **kwargs):
        """创建评论，添加权限验证"""
        # 获取视频ID
        video_id = request.data.get('video')
        if not video_id:
            return Response(
                {"detail": "缺少视频ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取视频对象
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response(
                {"detail": "视频不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查评论权限
        has_permission, error_message = check_comment_permission(video, request.user)
        if not has_permission:
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 继续正常的创建流程
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """回复评论"""
        parent_comment = self.get_object()
        video = parent_comment.video
        
        # 检查评论权限
        has_permission, error_message = check_comment_permission(video, request.user)
        if not has_permission:
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data={
            'video': video.id,
            'parent': parent_comment.id,
            'text': request.data.get('text')
        })
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            
            # 更新视频评论数
            video.comments_count = F('comments_count') + 1
            video.save(update_fields=['comments_count'])
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 创建分片上传的类视图
class ChunkUploadView(APIView):
    """视频分片上传视图"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        """处理分片上传"""
        chunk = request.FILES.get('chunk')
        file_name = request.POST.get('file_name')
        file_md5 = request.POST.get('file_md5')
        chunk_index = int(request.POST.get('chunk_index', 0))
        chunks_total = int(request.POST.get('chunks_total', 1))
        
        if not chunk or not file_name or not file_md5:
            return Response(
                {"detail": "缺少必要参数"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建用户上传目录
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'chunks', file_md5)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存分片文件
        chunk_file_path = os.path.join(temp_dir, f"{chunk_index}")
        with open(chunk_file_path, 'wb+') as destination:
            for chunk_data in chunk.chunks():
                destination.write(chunk_data)
        
        return Response({
            "detail": f"分片 {chunk_index + 1}/{chunks_total} 上传成功", 
            "chunk_index": chunk_index,
        })


class CheckFileView(APIView):
    """检查文件是否已存在视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """检查文件是否已上传"""
        file_name = request.data.get('file_name')
        file_md5 = request.data.get('file_md5')
        file_size = request.data.get('file_size')
        
        if not file_name or not file_md5 or not file_size:
            return Response(
                {"detail": "缺少必要参数"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否存在同MD5的视频
        video = Video.objects.filter(
            hls_file__contains=file_md5,
            user=request.user
        ).first()
        
        if video:
            # 文件已存在，直接返回视频信息
            serializer = VideoSerializer(video)
            return Response({
                "exists": True,
                "video": serializer.data
            })
        
        # 文件不存在，但检查是否有已上传的分片
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'chunks', file_md5)
        
        if os.path.exists(temp_dir):
            # 获取已上传的分片列表
            uploaded_chunks = []
            for filename in os.listdir(temp_dir):
                try:
                    chunk_index = int(filename)
                    uploaded_chunks.append(chunk_index)
                except ValueError:
                    continue
            
            return Response({
                "exists": False,
                "uploaded_chunks": uploaded_chunks
            })
        
        return Response({
            "exists": False,
            "uploaded_chunks": []
        })


class MergeChunksView(APIView):
    """合并文件分片视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """合并分片并创建视频记录"""
        from django.db import transaction
        
        file_name = request.data.get('file_name')
        file_md5 = request.data.get('file_md5')
        file_size = request.data.get('file_size')
        chunks_total = int(request.data.get('chunks_total', 1))
        
        if not file_name or not file_md5 or not file_size:
            return Response(
                {"detail": "缺少必要参数"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查分片是否全部上传
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'chunks', file_md5)
        
        if not os.path.exists(temp_dir):
            return Response(
                {"detail": "没有找到上传的分片"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查分片数量
        chunks = os.listdir(temp_dir)
        if len(chunks) != chunks_total:
            return Response(
                {"detail": f"分片不完整，预期 {chunks_total} 个，实际 {len(chunks)} 个"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建上传目录
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'uploads', 
                                 f"{timezone.now().year}",
                                 f"{timezone.now().month:02d}",
                                 f"{timezone.now().day:02d}")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 确定文件扩展名
        file_ext = os.path.splitext(file_name)[1]
        if not file_ext:
            file_ext = '.mp4'  # 默认使用mp4扩展名
        
        # 合并后的文件路径
        merged_filename = f"{file_md5}{file_ext}"
        merged_file_path = os.path.join(upload_dir, merged_filename)
        
        # 使用事务确保数据库和文件系统的一致性
        try:
            with transaction.atomic():
                # 合并分片
                with open(merged_file_path, 'wb') as target_file:
                    # 按索引顺序合并
                    for i in range(chunks_total):
                        chunk_path = os.path.join(temp_dir, str(i))
                        if os.path.exists(chunk_path):
                            with open(chunk_path, 'rb') as chunk_file:
                                target_file.write(chunk_file.read())
                
                # 创建视频记录
                video_file_path = os.path.join(
                    'videos', 'uploads',
                    f"{timezone.now().year}",
                    f"{timezone.now().month:02d}",
                    f"{timezone.now().day:02d}", 
                    merged_filename
                )
                
                video = Video.objects.create(
                    title=os.path.splitext(file_name)[0],  # 使用文件名作为标题
                    user=request.user,
                    video_file=video_file_path
                )
                
                # 记录视频ID和详细信息
                logger.info(f"新创建视频ID: {video.id}, 标题: {video.title}, 用户ID: {video.user.id}")
                
                # 清理临时分片（只有在数据库记录创建成功后才清理）
                shutil.rmtree(temp_dir)
                
                # 返回视频信息
                serializer = VideoDetailSerializer(
                    video, 
                    context={'request': request}
                )
                
                response_data = {
                    "detail": "文件合并成功",
                    "video": serializer.data
                }
                logger.info(f"合并分片API响应: {response_data}")
                
                return Response(response_data)
                
        except Exception as e:
            # 发生错误时清理已合并的文件
            logger.error(f"合并分片失败: {str(e)}")
            
            # 删除已合并的文件
            if os.path.exists(merged_file_path):
                try:
                    os.remove(merged_file_path)
                    logger.info(f"已清理失败的合并文件: {merged_file_path}")
                except Exception as cleanup_error:
                    logger.error(f"清理合并文件失败: {str(cleanup_error)}")
            
            # 保留临时分片，以便用户重试
            return Response(
                {"detail": f"文件合并失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoViewViewSet(viewsets.ModelViewSet):
    """视频观看记录视图集"""
    serializer_class = VideoViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HistoryListPagination  # 使用游标分页
    ordering = ['-view_date']  # 明确指定排序字段，游标分页必需
    
    def get_queryset(self):
        """获取当前用户的观看记录 - 优化查询"""
        # 优化：预加载视频和用户信息
        return VideoView.objects.filter(user=self.request.user).select_related(
            'video', 'video__user', 'video__category'
        ).prefetch_related('video__tags').order_by('-view_date')
    
    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """获取用户的观看历史"""
        queryset = self.get_queryset()
        
        # 处理搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(video__title__icontains=search)
        
        # 处理时间筛选
        time_filter = request.query_params.get('time_filter')
        if time_filter:
            now = timezone.now()
            if time_filter == 'today':
                # 今天的记录
                queryset = queryset.filter(view_date__date=now.date())
            elif time_filter == 'week':
                # 本周的记录
                week_start = now - timezone.timedelta(days=now.weekday())
                queryset = queryset.filter(view_date__gte=week_start)
            elif time_filter == 'month':
                # 本月的记录
                month_start = now.replace(day=1)
                queryset = queryset.filter(view_date__gte=month_start)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='clear')
    def clear_history(self, request):
        """清空观看历史"""
        VideoView.objects.filter(user=request.user).delete()
        return Response({"detail": "观看历史已清空"}, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """删除单条观看记录"""
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"detail": "您无权删除此记录"}, status=status.HTTP_403_FORBIDDEN)
        
        self.perform_destroy(instance)
        return Response({"detail": "记录已删除"}, status=status.HTTP_204_NO_CONTENT)


class VideoCollectionViewSet(viewsets.ModelViewSet):
    """视频收藏视图集"""
    serializer_class = VideoCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CollectionListPagination  # 使用标准分页
    
    def get_queryset(self):
        """获取当前用户的收藏记录 - 优化查询"""
        # 优化：预加载视频和用户信息
        return VideoCollection.objects.filter(user=self.request.user).select_related(
            'video', 'video__user', 'video__category'
        ).prefetch_related('video__tags').order_by('-created_at')
    
    @action(detail=False, methods=['get'], url_path='list')
    def collection_list(self, request):
        """获取用户的收藏列表"""
        queryset = self.get_queryset()
        
        # 处理搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(video__title__icontains=search)
        
        # 处理排序
        ordering = request.query_params.get('ordering')
        if ordering:
            if ordering == 'recent':
                queryset = queryset.order_by('-created_at')
            elif ordering == 'popular':
                queryset = queryset.order_by('-video__views_count')
            elif ordering == 'title':
                queryset = queryset.order_by('video__title')
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='clear')
    def clear_collections(self, request):
        """清空收藏列表"""
        VideoCollection.objects.filter(user=request.user).delete()
        return Response({"detail": "收藏列表已清空"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_collection(self, request, pk=None):
        """添加或取消收藏视频"""
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({"detail": "视频不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否已收藏
        collection = VideoCollection.objects.filter(user=request.user, video=video).first()
        
        if collection:
            # 已收藏，取消收藏
            collection.delete()
            return Response({"detail": "已取消收藏", "is_collected": False}, status=status.HTTP_200_OK)
        else:
            # 未收藏，添加收藏
            VideoCollection.objects.create(user=request.user, video=video)
            return Response({"detail": "收藏成功", "is_collected": True}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """删除单条收藏记录"""
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"detail": "您无权删除此记录"}, status=status.HTTP_403_FORBIDDEN)
        
        self.perform_destroy(instance)
        return Response({"detail": "收藏已删除"}, status=status.HTTP_204_NO_CONTENT)


class DanmakuViewSet(viewsets.ModelViewSet):
    """弹幕视图集
    
    TODO: 实现完整的弹幕功能
    - 弹幕列表获取
    - 弹幕发送
    - 弹幕举报
    - 敏感词过滤
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # TODO: 实现弹幕查询
        # return Danmaku.objects.filter(video_id=self.request.query_params.get('video_id'))
        from .models import Danmaku
        video_id = self.request.query_params.get('video_id')
        if video_id:
            return Danmaku.objects.filter(video_id=video_id).order_by('time')
        return Danmaku.objects.none()
    
    def list(self, request, *args, **kwargs):
        """获取视频弹幕列表"""
        video_id = request.query_params.get('video_id')
        if not video_id:
            return Response({"results": []})
        
        queryset = self.get_queryset()
        # TODO: 添加分页
        data = list(queryset.values('id', 'text', 'time', 'mode', 'color'))
        return Response({"results": data})
    
    def create(self, request, *args, **kwargs):
        """发送弹幕"""
        # TODO: 实现弹幕发送
        # - 敏感词过滤
        # - 频率限制
        from .models import Danmaku
        
        video_id = request.data.get('video')
        text = request.data.get('text', '').strip()
        time = request.data.get('time', 0)
        mode = request.data.get('mode', 0)
        color = request.data.get('color', '#FFFFFF')
        
        if not video_id or not text:
            return Response(
                {"detail": "缺少必要参数"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: 敏感词过滤
        
        danmaku = Danmaku.objects.create(
            video_id=video_id,
            user=request.user if request.user.is_authenticated else None,
            text=text,
            time=time,
            mode=mode,
            color=color
        )
        
        return Response({
            "id": danmaku.id,
            "text": danmaku.text,
            "time": danmaku.time,
            "mode": danmaku.mode,
            "color": danmaku.color
        }, status=status.HTTP_201_CREATED)
