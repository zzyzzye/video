"""
AI 服务异步任务
使用 Celery shared_task 装饰器定义任务
"""
import os
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import ModerationResult, VideoSummary
from .services import WhisperService, OCRService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def generate_video_subtitles(self, video_id, language='auto'):
    """
    生成视频字幕（使用 Whisper）
    
    Args:
        video_id: 视频ID
        language: 语言代码（'auto' 为自动检测）
    """
    from videos.models import Video
    
    task_id = self.request.id or 'unknown'
    logger.info(f"[Task {task_id}] 开始生成字幕: video_id={video_id}")
    
    tmp_wav_path = None
    whisper = None
    
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            logger.error(f"[Task {task_id}] 视频文件不存在")
            return {"status": "error", "reason": "file_not_found"}
        
        video_file_path = video.video_file.path
        if not os.path.exists(video_file_path):
            logger.error(f"[Task {task_id}] 视频文件路径无效: {video_file_path}")
            return {"status": "error", "reason": "file_not_found"}
        
        # 创建临时目录
        tmp_dir = Path(settings.MEDIA_ROOT) / 'tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_wav_path = tmp_dir / f"whisper_{video_id}_{task_id}.wav"
        
        # 初始化 Whisper 服务
        whisper = WhisperService()
        
        # 提取音频
        logger.info(f"[Task {task_id}] 提取音频...")
        whisper.extract_audio(video_file_path, tmp_wav_path)
        
        # 生成字幕
        logger.info(f"[Task {task_id}] 生成字幕...")
        result = whisper.generate_subtitles(str(tmp_wav_path), language=language)
        
        # 更新视频字幕信息
        video.subtitles_draft = result['subtitles']
        video.has_subtitle = len(result['subtitles']) > 0
        video.subtitle_type = 'soft' if video.has_subtitle else 'none'
        video.subtitle_language = result['language']
        video.subtitle_detected_at = timezone.now()
        
        if video.status == 'uploading':
            video.status = 'pending_subtitle_edit'
        
        video.save(update_fields=[
            'subtitles_draft',
            'has_subtitle',
            'subtitle_type',
            'subtitle_language',
            'subtitle_detected_at',
            'status'
        ])
        
        logger.info(f"[Task {task_id}] 字幕生成完成: count={result['count']}, language={result['language']}")
        
        return {
            "status": "success",
            "video_id": video_id,
            "count": result['count'],
            "subtitle_language": result['language'],
        }
        
    except Video.DoesNotExist:
        logger.error(f"[Task {task_id}] 视频不存在: video_id={video_id}")
        return {"status": "error", "reason": "video_not_found"}
    
    except Exception as e:
        logger.error(f"[Task {task_id}] 字幕生成失败: {str(e)}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            logger.warning(f"[Task {task_id}] 将重试...")
            raise self.retry(exc=e)
        
        return {"status": "error", "reason": str(e)}
    
    finally:
        # 清理临时文件
        if tmp_wav_path and os.path.exists(tmp_wav_path):
            try:
                os.remove(tmp_wav_path)
                logger.info(f"[Task {task_id}] 已删除临时音频文件")
            except Exception:
                pass
        
        # 释放 Whisper 模型
        if whisper:
            whisper.release_model()


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def detect_video_subtitle(self, video_id):
    """
    检测视频字幕（软字幕 + 硬字幕）
    
    Args:
        video_id: 视频ID
    """
    from videos.models import Video
    
    task_id = self.request.id or 'unknown'
    logger.info(f"[Task {task_id}] 开始字幕检测: video_id={video_id}")
    
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            logger.error(f"[Task {task_id}] 视频文件不存在")
            # 字幕检测失败，但允许继续（设置为无字幕）
            video.has_subtitle = False
            video.subtitle_type = 'none'
            video.subtitle_language = ''
            video.status = 'pending_subtitle_edit'
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status'])
            return {
                "status": "error",
                "reason": "file_not_found",
                "allow_continue": True,
                "subtitle_info": {
                    "has_subtitle": False,
                    "subtitle_type": "none",
                    "subtitle_language": ""
                }
            }
        
        video_file_path = video.video_file.path
        if not os.path.exists(video_file_path):
            logger.error(f"[Task {task_id}] 视频文件路径无效: {video_file_path}")
            # 字幕检测失败，但允许继续
            video.has_subtitle = False
            video.subtitle_type = 'none'
            video.subtitle_language = ''
            video.status = 'pending_subtitle_edit'
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status'])
            return {
                "status": "error",
                "reason": "file_not_found",
                "allow_continue": True,
                "subtitle_info": {
                    "has_subtitle": False,
                    "subtitle_type": "none",
                    "subtitle_language": ""
                }
            }
        
        logger.info(f"[Task {task_id}] 视频文件: {video_file_path}")
        
        # 使用 OCR 服务检测字幕
        ocr = OCRService()
        result = ocr.detect_subtitle(video_file_path)
        
        logger.info(f"[Task {task_id}] 检测结果: {result}")
        
        # 更新视频字幕信息
        video.has_subtitle = result['has_subtitle']
        video.subtitle_type = result['subtitle_type']
        video.subtitle_language = result['subtitle_language']
        video.subtitle_detected_at = timezone.now()
        
        # 根据检测结果设置视频状态
        if not result['has_subtitle'] or result['subtitle_type'] == 'soft':
            video.status = 'pending_subtitle_edit'
            logger.info(f"[Task {task_id}] 设置状态为 pending_subtitle_edit")
            
            video.save(update_fields=[
                'has_subtitle',
                'subtitle_type',
                'subtitle_language',
                'subtitle_detected_at',
                'status'
            ])
            
        elif result['subtitle_type'] == 'hard':
            video.status = 'processing'
            logger.info(f"[Task {task_id}] 检测到硬字幕，设置状态为 processing")
            
            video.save(update_fields=[
                'has_subtitle',
                'subtitle_type',
                'subtitle_language',
                'subtitle_detected_at',
                'status'
            ])
            
            # 触发转码任务
            from videos.tasks import process_video
            try:
                process_video.delay(video_id)
                logger.info(f"[Task {task_id}] 已触发转码任务")
            except Exception as e:
                logger.error(f"[Task {task_id}] 触发转码任务失败: {e}")
                video.status = 'uploaded'
                video.save(update_fields=['status'])
                raise
        else:
            video.save(update_fields=[
                'has_subtitle',
                'subtitle_type',
                'subtitle_language',
                'subtitle_detected_at'
            ])
        
        logger.info(f"[Task {task_id}] 字幕检测完成: has_subtitle={result['has_subtitle']}, type={result['subtitle_type']}")
        
        return {
            "status": "success",
            "video_id": video_id,
            "subtitle_info": {
                "has_subtitle": result['has_subtitle'],
                "subtitle_type": result['subtitle_type'],
                "subtitle_language": result['subtitle_language']
            },
            "video_status": video.status
        }
        
    except Video.DoesNotExist:
        logger.error(f"[Task {task_id}] 视频不存在: video_id={video_id}")
        return {
            "status": "error",
            "reason": "video_not_found",
            "allow_continue": False,
            "subtitle_info": {
                "has_subtitle": False,
                "subtitle_type": "none",
                "subtitle_language": ""
            }
        }
    
    except Exception as e:
        logger.error(f"[Task {task_id}] 字幕检测失败: {str(e)}", exc_info=True)
        
        # 如果还有重试次数，继续重试
        if self.request.retries < self.max_retries:
            logger.warning(f"[Task {task_id}] 将重试...")
            raise self.retry(exc=e)
        
        # 重试次数用完，设置为无字幕状态，允许用户继续
        try:
            video = Video.objects.get(id=video_id)
            video.has_subtitle = False
            video.subtitle_type = 'none'
            video.subtitle_language = ''
            video.status = 'pending_subtitle_edit'
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status'])
            logger.warning(f"[Task {task_id}] 字幕检测失败，已设置为无字幕状态，允许用户继续")
        except Exception as save_error:
            logger.error(f"[Task {task_id}] 保存失败状态时出错: {save_error}")
        
        return {
            "status": "error",
            "reason": str(e),
            "allow_continue": True,
            "subtitle_info": {
                "has_subtitle": False,
                "subtitle_type": "none",
                "subtitle_language": ""
            }
        }


@shared_task
def moderate_video_task(video_id):
    """异步执行视频内容审核"""
    try:
        logger.info(f"开始审核视频 {video_id}")
        
        # TODO: 实现 AI 审核逻辑
        moderation = ModerationResult.objects.create(
            video_id=video_id,
            status='processing'
        )
        
        moderation.status = 'completed'
        moderation.result = 'safe'
        moderation.confidence = 0.95
        moderation.save()
        
        logger.info(f"视频 {video_id} 审核完成")
        return {'video_id': video_id, 'status': 'completed'}
        
    except Exception as e:
        logger.error(f"视频 {video_id} 审核失败: {str(e)}")
        if 'moderation' in locals():
            moderation.status = 'failed'
            moderation.error_message = str(e)
            moderation.save()
        raise


@shared_task
def summarize_video_task(video_id):
    """异步生成视频摘要"""
    try:
        logger.info(f"开始生成视频 {video_id} 摘要")
        
        # TODO: 实现视频摘要逻辑
        summary, created = VideoSummary.objects.get_or_create(
            video_id=video_id,
            defaults={
                'summary': 'AI 生成的摘要',
                'key_frames': [],
                'auto_tags': []
            }
        )
        
        logger.info(f"视频 {video_id} 摘要生成完成")
        return {'video_id': video_id, 'status': 'completed'}
        
    except Exception as e:
        logger.error(f"视频 {video_id} 摘要生成失败: {str(e)}")
        raise


@shared_task
def batch_moderate_videos(video_ids):
    """批量审核视频"""
    results = []
    for video_id in video_ids:
        try:
            result = moderate_video_task.delay(video_id)
            results.append({'video_id': video_id, 'task_id': result.id})
        except Exception as e:
            logger.error(f"提交视频 {video_id} 审核任务失败: {str(e)}")
            results.append({'video_id': video_id, 'error': str(e)})
    
    return results
