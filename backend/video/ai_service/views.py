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
    
    @action(detail=True, methods=['post'], url_path='moderate')
    def moderate_video(self, request, pk=None):
        """
        AI 视频内容审核
        检测 NSFW、暴力、敏感内容等
        """
        # TODO: 实现 AI 审核逻辑
        result = {
            'video_id': pk,
            'is_safe': True,
            'confidence': 0.95,
            'categories': {
                'nsfw': 0.02,
                'violence': 0.01,
                'sensitive': 0.03
            },
            'flagged_frames': [],
            'message': 'AI 审核功能开发中'
        }
        
        serializer = ModerationResultSerializer(data=result)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='result')
    def get_result(self, request, pk=None):
        """获取视频审核结果"""
        # TODO: 从数据库获取审核结果
        result = {
            'video_id': pk,
            'is_safe': True,
            'confidence': 0.0,
            'categories': {},
            'flagged_frames': [],
            'message': '暂无审核记录'
        }
        
        serializer = ModerationResultSerializer(data=result)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
