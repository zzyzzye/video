from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Video
from .serializers import VideoDetailSerializer
from users.utils.log_utils import log_video_review

class IsAdminUser(permissions.BasePermission):
    """
    自定义权限类，只允许管理员用户访问
    """
    def has_permission(self, request, view):
        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 检查用户角色是否为admin或superadmin
        user_role = getattr(request.user, 'role', None)
        
        # 打印调试信息
        print(f"用户 {request.user.username} 权限检查:")
        print(f"- role: {user_role}")
        
        # 只检查role属性
        return user_role in ['admin', 'superadmin']

class AdminVideoViewSet(viewsets.ViewSet):
    """
    管理员视频管理视图集
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_pending_videos(self, request):
        """
        获取待审核的视频列表
        """
        queryset = Video.objects.filter(status='pending').select_related('user', 'category', 'reviewer').prefetch_related('tags').order_by('-created_at')
        
        # 处理搜索参数
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(user__username__icontains=search)
        
        # 处理分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        videos = queryset[start:end]
        
        serializer = VideoDetailSerializer(videos, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })
    
    def get_reviewed_videos(self, request):
        """
        获取已审核的视频列表
        """
        # 获取状态参数
        status_param = request.query_params.get('status', 'approved')
        if status_param not in ['approved', 'rejected']:
            return Response({'error': '无效的状态参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Video.objects.filter(status=status_param).select_related('user', 'category', 'reviewer').prefetch_related('tags').order_by('-created_at')
        
        # 处理搜索参数
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(user__username__icontains=search)
        
        # 处理分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        videos = queryset[start:end]
        
        serializer = VideoDetailSerializer(videos, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })
    
    def approve_video(self, request, video_id):
        """
        审核通过视频
        """
        video = get_object_or_404(Video, id=video_id)
        
        if video.status != 'pending':
            return Response({'error': '只能审核待审核状态的视频'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新视频状态
        video.status = 'approved'
        video.reviewed_at = timezone.now()
        video.reviewer = request.user
        
        # 审核通过后自动发布视频
        video.is_published = True
        if not video.published_at:
            video.published_at = timezone.now()
        
        # 获取备注信息
        remark = request.data.get('remark', '')
        video.review_remark = remark
        
        video.save()
        
        # 记录日志
        log_video_review(
            operator=request.user,
            video=video,
            status='approved',
            request=request
        )
        
        return Response({'message': '视频审核通过成功'})
    
    def reject_video(self, request, video_id):
        """
        拒绝视频
        """
        video = get_object_or_404(Video, id=video_id)
        
        if video.status != 'pending':
            return Response({'error': '只能审核待审核状态的视频'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取拒绝原因
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'error': '请提供拒绝原因'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新视频状态
        video.status = 'rejected'
        video.reviewed_at = timezone.now()
        video.reviewer = request.user
        video.review_remark = reason
        
        video.save()
        
        # 记录日志
        log_video_review(
            operator=request.user,
            video=video,
            status='rejected',
            request=request
        )
        
        return Response({'message': '视频已拒绝'}) 