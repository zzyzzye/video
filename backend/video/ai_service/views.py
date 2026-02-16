"""
AI 服务视图
使用 ViewSet 组织 API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from celery.result import AsyncResult
import logging

from .serializers import (
    ModerationResultSerializer,
    FrameRecognitionSerializer,
    FrameRecognitionResultSerializer,
    VideoSummarySerializer
)
from .services import WhisperService, OCRService

logger = logging.getLogger(__name__)


class ModerationViewSet(viewsets.ViewSet):
    """AI 内容审核视图集"""
    
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """
        获取 AI 审核列表
        
        查询参数:
        - status: 审核状态 (pending/processing/completed/failed)
        - result: 审核结果 (safe/unsafe/uncertain)
        - show_unreviewed: 是否显示未审核的视频 (true/false)
        - page: 页码
        - page_size: 每页数量
        """
        from .models import ModerationResult
        from .serializers import ModerationListSerializer, ModerationStatsSerializer
        from videos.models import Video
        from django.db.models import Q, Count, OuterRef, Exists
        
        # 获取查询参数
        status_filter = request.query_params.get('status', '')
        result_filter = request.query_params.get('result', '')
        show_unreviewed = request.query_params.get('show_unreviewed', 'true').lower() == 'true'
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # 如果显示未审核视频，需要包含没有审核记录的视频
        if show_unreviewed:
            # 获取所有待审核的视频（状态为 pending 或 uploading）
            pending_videos = Video.objects.filter(
                Q(status='pending') | Q(status='uploading'),
                is_published=False
            ).exclude(
                ai_moderations__isnull=False
            ).select_related('user')
            
            # 为这些视频创建虚拟的审核记录（不保存到数据库）
            virtual_moderations = []
            for video in pending_videos:
                virtual_moderations.append({
                    'id': None,
                    'video': video,
                    'status': 'pending',
                    'result': None,
                    'confidence': 0.0,
                    'neutral_score': 0.0,
                    'low_score': 0.0,
                    'medium_score': 0.0,
                    'high_score': 0.0,
                    'flagged_frames': [],
                    'created_at': None,  # 未审核，没有审核创建时间
                    'updated_at': None,  # 未审核，没有审核更新时间
                    'video_created_at': video.created_at,  # 保存视频创建时间用于排序
                })
        
        # 构建查询
        queryset = ModerationResult.objects.select_related('video', 'video__user').all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if result_filter:
            queryset = queryset.filter(result=result_filter)
        
        # 统计数据
        stats = ModerationResult.objects.aggregate(
            pending=Count('id', filter=Q(status='pending')),
            processing=Count('id', filter=Q(status='processing')),
            safe=Count('id', filter=Q(result='safe')),
            unsafe=Count('id', filter=Q(result='unsafe')),
            uncertain=Count('id', filter=Q(result='uncertain')),
            total=Count('id')
        )
        
        # 添加未审核视频数量
        if show_unreviewed:
            unreviewed_count = Video.objects.filter(
                Q(status='pending') | Q(status='uploading'),
                is_published=False
            ).exclude(
                ai_moderations__isnull=False
            ).count()
            stats['pending'] = stats.get('pending', 0) + unreviewed_count
            stats['total'] = stats.get('total', 0) + unreviewed_count
        
        # 合并虚拟审核记录和真实审核记录
        if show_unreviewed and not status_filter and not result_filter:
            # 转换 queryset 为列表
            real_moderations = list(queryset)
            all_moderations = virtual_moderations + real_moderations
            
            # 排序（按时间倒序，虚拟记录使用视频创建时间，真实记录使用审核更新时间）
            def get_sort_time(x):
                if isinstance(x, dict):
                    # 虚拟记录：使用视频创建时间
                    return x.get('video_created_at')
                else:
                    # 真实记录：使用审核更新时间
                    return x.updated_at
            
            all_moderations.sort(key=get_sort_time, reverse=True)
            
            # 分页
            total = len(all_moderations)
            start = (page - 1) * page_size
            end = start + page_size
            results = all_moderations[start:end]
            
            # 序列化
            serialized_results = []
            for item in results:
                if isinstance(item, dict):
                    # 虚拟审核记录（未审核的视频）
                    serialized_results.append({
                        'id': None,
                        'video': {
                            'id': item['video'].id,
                            'title': item['video'].title,
                            'thumbnail': request.build_absolute_uri(item['video'].thumbnail.url) if item['video'].thumbnail else None,
                            'created_at': item['video'].created_at.isoformat(),
                            'user': {
                                'id': item['video'].user.id,
                                'username': item['video'].user.username,
                            } if item['video'].user else None
                        },
                        'status': 'pending',
                        'result': None,
                        'confidence': 0.0,
                        'neutral_score': 0.0,
                        'low_score': 0.0,
                        'medium_score': 0.0,
                        'high_score': 0.0,
                        'flagged_frames': [],
                        'created_at': None,  # 未审核，无审核创建时间
                        'updated_at': None,  # 未审核，无审核更新时间
                    })
                else:
                    # 真实审核记录
                    serializer = ModerationListSerializer(item, context={'request': request})
                    serialized_results.append(serializer.data)
        else:
            # 只显示真实审核记录
            total = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            results = queryset[start:end]
            serializer = ModerationListSerializer(results, many=True, context={'request': request})
            serialized_results = serializer.data
        
        stats_serializer = ModerationStatsSerializer(data=stats)
        stats_serializer.is_valid()
        
        return Response({
            'count': total,
            'results': serialized_results,
            'stats': stats_serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """获取 AI 审核详情"""
        from .models import ModerationResult
        from .serializers import ModerationResultSerializer
        
        try:
            moderation = ModerationResult.objects.select_related('video', 'video__user').get(pk=pk)
            serializer = ModerationResultSerializer(moderation, context={'request': request})
            return Response(serializer.data)
        except ModerationResult.DoesNotExist:
            return Response(
                {'detail': '审核记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='submit-review')
    def submit_review(self, request):
        """
        提交 AI 审核结果到人工审核
        
        请求参数:
        - moderation_id: AI 审核记录 ID
        - action: 操作 (approve/reject)
        - remark: 备注
        """
        from .models import ModerationResult
        from videos.models import Video
        
        moderation_id = request.data.get('moderation_id')
        action = request.data.get('action')  # approve/reject
        remark = request.data.get('remark', '')
        
        if not moderation_id or not action:
            return Response(
                {'detail': '缺少必要参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action not in ['approve', 'reject']:
            return Response(
                {'detail': 'action 必须是 approve 或 reject'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            moderation = ModerationResult.objects.select_related('video').get(pk=moderation_id)
            video = moderation.video
            
            # 更新视频状态
            if action == 'approve':
                video.status = 'approved'
                video.is_published = True
            else:
                video.status = 'rejected'
                video.is_published = False
            
            video.reviewer = request.user
            video.reviewed_at = timezone.now()
            video.review_remark = remark
            video.save(update_fields=['status', 'is_published', 'reviewer', 'reviewed_at', 'review_remark'])
            
            return Response({
                'detail': f'视频已{("通过" if action == "approve" else "拒绝")}',
                'video_id': video.id,
                'status': video.status
            })
            
        except ModerationResult.DoesNotExist:
            return Response(
                {'detail': 'AI 审核记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"提交审核失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'提交审核失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='revoke-review')
    def revoke_review(self, request):
        """
        撤销审核结果
        
        请求参数:
        - moderation_id: AI 审核记录 ID
        """
        from .models import ModerationResult
        from videos.models import Video
        
        moderation_id = request.data.get('moderation_id')
        
        if not moderation_id:
            return Response(
                {'detail': '缺少 moderation_id 参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            moderation = ModerationResult.objects.select_related('video').get(pk=moderation_id)
            video = moderation.video
            
            # 检查视频是否已审核
            if video.status not in ['approved', 'rejected']:
                return Response(
                    {'detail': '该视频未进行人工审核，无需撤销'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 恢复到审核前的状态
            video.status = 'pending'
            video.is_published = False
            video.reviewer = None
            video.reviewed_at = None
            video.review_remark = ''
            video.save(update_fields=['status', 'is_published', 'reviewer', 'reviewed_at', 'review_remark'])
            
            return Response({
                'detail': '审核结果已撤销',
                'video_id': video.id,
                'status': video.status
            })
            
        except ModerationResult.DoesNotExist:
            return Response(
                {'detail': 'AI 审核记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"撤销审核失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'撤销审核失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='re-moderate')
    def re_moderate(self, request):
        """
        重新审核视频（覆盖之前的审核结果）
        
        请求参数:
        - moderation_id: 原审核记录 ID
        - threshold_level: 检测级别 (可选)
        - threshold: 置信度阈值 (可选)
        - fps: 每秒抽帧数 (可选)
        """
        from .models import ModerationResult
        from .tasks import moderate_video_task
        
        moderation_id = request.data.get('moderation_id')
        if not moderation_id:
            return Response(
                {'detail': '缺少 moderation_id 参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            moderation = ModerationResult.objects.select_related('video').get(pk=moderation_id)
            video = moderation.video
            
            # 获取参数（如果没有提供，使用之前的参数）
            old_details = moderation.details or {}
            threshold_level = request.data.get('threshold_level', old_details.get('threshold_level', 'medium'))
            threshold = float(request.data.get('threshold', old_details.get('threshold', 0.6)))
            fps = int(request.data.get('fps', old_details.get('fps', 1)))
            
            # 验证参数
            if threshold_level not in ['low', 'medium', 'high']:
                return Response(
                    {'detail': 'threshold_level 必须是 low/medium/high'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not 0 <= threshold <= 1:
                return Response(
                    {'detail': 'threshold 必须在 0-1 之间'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if fps < 1 or fps > 10:
                return Response(
                    {'detail': 'fps 必须在 1-10 之间'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 重置审核状态
            moderation.status = 'processing'
            moderation.result = None
            moderation.confidence = 0.0
            moderation.neutral_score = 0.0
            moderation.low_score = 0.0
            moderation.medium_score = 0.0
            moderation.high_score = 0.0
            moderation.flagged_frames = []
            moderation.error_message = ''
            moderation.save()
            
            # 提交新的审核任务
            async_result = moderate_video_task.delay(video.id, threshold_level, threshold, fps)
            
            return Response({
                'detail': '重新审核任务已提交',
                'video_id': video.id,
                'moderation_id': moderation.id,
                'task_id': async_result.id,
                'params': {
                    'threshold_level': threshold_level,
                    'threshold': threshold,
                    'fps': fps
                }
            })
            
        except ModerationResult.DoesNotExist:
            return Response(
                {'detail': 'AI 审核记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"重新审核失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'重新审核失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='moderate')
    def moderate_video(self, request):
        """
        提交视频审核任务
        
        请求参数:
        - video_id: 视频 ID (必需)
        - threshold_level: 检测级别 (可选, 默认 medium)
        - threshold: 置信度阈值 (可选, 默认 0.6)
        - fps: 每秒抽帧数 (可选, 默认 1)
        """
        from videos.models import Video
        from .tasks import moderate_video_task
        
        video_id = request.data.get('video_id')
        if not video_id:
            return Response(
                {'detail': '缺少 video_id 参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查视频是否存在
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response(
                {'detail': '视频不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 获取参数
        threshold_level = request.data.get('threshold_level', 'medium')
        threshold = float(request.data.get('threshold', 0.6))
        fps = int(request.data.get('fps', 1))
        
        # 验证参数
        if threshold_level not in ['low', 'medium', 'high']:
            return Response(
                {'detail': 'threshold_level 必须是 low/medium/high'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not 0 <= threshold <= 1:
            return Response(
                {'detail': 'threshold 必须在 0-1 之间'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if fps < 1 or fps > 10:
            return Response(
                {'detail': 'fps 必须在 1-10 之间'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 提交异步任务
            async_result = moderate_video_task.delay(video_id, threshold_level, threshold, fps)
            
            return Response({
                'detail': '审核任务已提交',
                'video_id': video_id,
                'task_id': async_result.id,
                'params': {
                    'threshold_level': threshold_level,
                    'threshold': threshold,
                    'fps': fps
                }
            })
        except Exception as e:
            logger.error(f"提交审核任务失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'提交审核任务失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='batch')
    def batch_moderate(self, request):
        """
        批量审核视频
        
        请求参数:
        - video_ids: 视频 ID 列表 (必需)
        - threshold_level: 检测级别 (可选)
        - threshold: 置信度阈值 (可选)
        - fps: 每秒抽帧数 (可选)
        """
        from .tasks import batch_moderate_videos
        
        video_ids = request.data.get('video_ids', [])
        if not video_ids or not isinstance(video_ids, list):
            return Response(
                {'detail': 'video_ids 必须是非空数组'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        threshold_level = request.data.get('threshold_level', 'medium')
        threshold = float(request.data.get('threshold', 0.6))
        fps = int(request.data.get('fps', 1))
        
        try:
            result = batch_moderate_videos.delay(video_ids, threshold_level, threshold, fps)
            
            return Response({
                'detail': f'已提交 {len(video_ids)} 个审核任务',
                'task_id': result.id,
                'video_count': len(video_ids)
            })
        except Exception as e:
            logger.error(f"批量审核失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'批量审核失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='task-status')
    def task_status(self, request):
        """
        查询审核任务状态
        
        查询参数:
        - task_id: 任务 ID (必需)
        """
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'detail': '缺少 task_id 参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from celery.result import AsyncResult
            result = AsyncResult(task_id)
            
            data = {
                'task_id': task_id,
                'state': result.state,
            }
            
            if result.state == 'SUCCESS':
                data['result'] = result.result or {}
            elif result.state == 'FAILURE':
                data['error'] = str(result.result)
            
            return Response(data)
        except Exception as e:
            logger.error(f"查询任务状态失败: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'查询任务状态失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecognitionViewSet(viewsets.ViewSet):
    """AI 画面识别视图集"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='frame')
    def recognize_frame(self, request):
        """
        AI 画面识别
        识别视频帧中的物体、场景、文字等
        """
        serializer = FrameRecognitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: 实现画面识别逻辑
        result = {
            'detected_objects': ['人物', '建筑', '天空'],
            'scene': '城市街景',
            'text': '',
            'faces': [],
            'confidence': 0.88
        }
        
        result_serializer = FrameRecognitionResultSerializer(data=result)
        if result_serializer.is_valid():
            return Response(result_serializer.data, status=status.HTTP_200_OK)
        return Response(result_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SummaryViewSet(viewsets.ViewSet):
    """AI 视频摘要视图集"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='generate')
    def summarize_video(self, request, pk=None):
        """
        AI 视频摘要
        生成视频内容摘要和关键帧
        """
        # TODO: 实现视频摘要逻辑
        result = {
            'video_id': pk,
            'summary': 'AI 视频摘要功能开发中',
            'key_frames': [],
            'tags': ['待分析'],
            'duration': 0.0
        }
        
        serializer = VideoSummarySerializer(data=result)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubtitleViewSet(viewsets.ViewSet):
    """字幕相关视图集"""
    
    permission_classes = [IsAuthenticated]
    
    def _get_video(self, video_id):
        """获取视频对象"""
        from videos.models import Video
        return get_object_or_404(Video, id=video_id)
    
    def _check_video_permission(self, video, user, allow_staff=True):
        """检查视频权限"""
        if allow_staff and user.is_staff:
            return True
        return video.user == user
    
    @action(detail=True, methods=['post'], url_path='detect')
    def detect(self, request, pk=None):
        """
        检测视频字幕（软字幕 + 硬字幕）
        
        返回任务 ID，前端可以轮询任务状态
        """
        video = self._get_video(pk)
        
        # 权限检查：只有视频所有者可以检测
        if not self._check_video_permission(video, request.user, allow_staff=False):
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
            
            # 提交异步任务
            from .tasks import detect_video_subtitle
            async_result = detect_video_subtitle.delay(video.id)
            
            logger.info(f"字幕检测任务已提交，task_id: {async_result.id}")
            
            return Response({
                "detail": "字幕检测任务已提交",
                "video_id": video.id,
                "task_id": async_result.id,
                "tip": "使用 detection-status 接口查询检测进度"
            })
            
        except Exception as e:
            logger.error(f"提交字幕检测任务失败: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"提交字幕检测任务失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='detection-status')
    def detection_status(self, request, pk=None):
        """
        查询字幕检测任务状态
        
        参数：
        - task_id: 任务 ID（必需）
        
        返回：
        - state: PENDING, STARTED, SUCCESS, FAILURE
        - result: 检测结果（成功时）
        - error: 错误信息（失败时）
        - allow_continue: 是否允许继续（失败时）
        """
        video = self._get_video(pk)
        
        # 权限检查
        if not self._check_video_permission(video, request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {"detail": "缺少 task_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from celery.result import AsyncResult
            result = AsyncResult(task_id)
            
            data = {
                "video_id": video.id,
                "task_id": task_id,
                "state": result.state,
            }
            
            if result.state == 'SUCCESS':
                payload = result.result or {}
                data["result"] = payload
                data["allow_continue"] = payload.get('allow_continue', True)
            elif result.state == 'FAILURE':
                error_info = result.result or {}
                if isinstance(error_info, dict):
                    data["error"] = error_info.get('reason', str(error_info))
                    data["allow_continue"] = error_info.get('allow_continue', True)
                else:
                    data["error"] = str(error_info)
                    data["allow_continue"] = True
            
            return Response(data)
        except Exception as e:
            logger.error(f"查询检测状态失败: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"查询检测状态失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get', 'put'], url_path='data')
    def data(self, request, pk=None):
        """
        获取或保存视频字幕（JSON 格式）
        
        GET: 返回字幕 JSON 数组
        PUT: 保存字幕 JSON 数组
        """
        video = self._get_video(pk)
        
        # 权限检查：视频所有者或管理员
        if not self._check_video_permission(video, request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            return Response({
                "video_id": video.id,
                "subtitles": video.subtitles_draft or []
            })
        
        # PUT 请求：保存字幕
        subtitles = request.data.get('subtitles')
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
        
        # 基础校验
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
        
        # 保存字幕
        video.subtitles_draft = subtitles
        video.has_subtitle = len(subtitles) > 0
        video.subtitle_type = 'soft' if video.has_subtitle else 'none'
        video.save(update_fields=['subtitles_draft', 'has_subtitle', 'subtitle_type'])
        
        return Response({
            "detail": "字幕已保存",
            "video_id": video.id,
            "count": len(subtitles)
        })
    
    @action(detail=True, methods=['get'], url_path='vtt')
    def vtt(self, request, pk=None):
        """
        输出 WebVTT 格式字幕文件（用于播放器）
        """
        video = self._get_video(pk)
        
        # 权限检查：公开视频或视频所有者或管理员
        if not video.is_published and not self._check_video_permission(video, request.user):
            return Response(
                {"detail": "无权访问此视频"},
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
    
    @action(detail=True, methods=['post'], url_path='generate')
    def generate(self, request, pk=None):
        """
        异步生成视频字幕（使用 Whisper）
        
        请求参数：
        - language: 语言代码（可选，默认 'auto' 自动检测）
          支持的语言：zh（中文）、en（英语）、ja（日语）、ko（韩语）等
          传入 'auto' 或不传则自动检测语言
        
        示例：
        POST /api/ai/subtitles/{video_id}/generate/
        {
            "language": "zh"  // 可选，不传则自动检测
        }
        """
        video = self._get_video(pk)
        
        # 权限检查：视频所有者或管理员
        if not self._check_video_permission(video, request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not video.video_file:
            return Response(
                {"detail": "视频文件不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取语言参数，默认自动检测
        language = request.data.get('language', 'auto')
        
        # 支持的语言列表（Whisper 支持的主要语言）
        supported_languages = [
            'auto', 'zh', 'en', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 
            'ar', 'pt', 'it', 'nl', 'pl', 'tr', 'vi', 'th', 'id'
        ]
        
        # 验证语言参数
        if language and language not in supported_languages:
            return Response(
                {
                    "detail": f"不支持的语言代码: {language}",
                    "supported_languages": supported_languages,
                    "tip": "使用 'auto' 可自动检测语言"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .tasks import generate_video_subtitles
            async_result = generate_video_subtitles.delay(video.id, language=language)
            
            return Response({
                "detail": "字幕生成任务已提交",
                "video_id": video.id,
                "task_id": async_result.id,
                "language": language,
                "tip": "使用 task-status 接口查询生成进度"
            })
        except Exception as e:
            logger.error(f"提交字幕生成任务失败: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"提交字幕生成任务失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='task-status')
    def task_status(self, request, pk=None):
        """
        查询字幕生成任务状态
        """
        video = self._get_video(pk)
        
        # 权限检查：视频所有者或管理员
        if not self._check_video_permission(video, request.user):
            return Response(
                {"detail": "无权操作此视频"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {"detail": "缺少 task_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = AsyncResult(task_id)
            
            data = {
                "video_id": video.id,
                "task_id": task_id,
                "state": result.state,
            }
            
            if result.state == 'SUCCESS':
                payload = result.result or {}
                data["result"] = payload
                data["subtitle_count"] = len(video.subtitles_draft or [])
            elif result.state in ('FAILURE',):
                data["error"] = str(result.result)
            
            return Response(data)
        except Exception as e:
            logger.error(f"查询任务状态失败: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"查询任务状态失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
