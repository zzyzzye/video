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
            video.is_published = False  # 重置发布状态
        
        video.save(update_fields=[
            'subtitles_draft',
            'has_subtitle',
            'subtitle_type',
            'subtitle_language',
            'subtitle_detected_at',
            'status',
            'is_published'
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
            video.is_published = False
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status', 'is_published'])
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
            video.is_published = False
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status', 'is_published'])
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
            video.is_published = False
            logger.info(f"[Task {task_id}] 设置状态为 pending_subtitle_edit")
            
            video.save(update_fields=[
                'has_subtitle',
                'subtitle_type',
                'subtitle_language',
                'subtitle_detected_at',
                'status',
                'is_published'
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
            video.is_published = False
            video.save(update_fields=['has_subtitle', 'subtitle_type', 'subtitle_language', 'status', 'is_published'])
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


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def moderate_video_task(self, video_id, threshold_level='medium', threshold=0.6, fps=1):
    """
    异步执行视频 NSFW 内容审核
    
    Args:
        video_id: 视频 ID
        threshold_level: 检测级别 (low/medium/high)
        threshold: 置信度阈值
        fps: 每秒抽取帧数
    """
    from videos.models import Video
    from .services import NSFWDetector
    from django.conf import settings
    
    task_id = self.request.id or 'unknown'
    logger.info(f"[Task {task_id}] 开始 NSFW 审核: video_id={video_id}")
    
    moderation = None
    detector = NSFWDetector()
    frames_dir = None
    
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.video_file:
            raise ValueError("视频文件不存在")
        
        video_file_path = video.video_file.path
        if not os.path.exists(video_file_path):
            raise ValueError(f"视频文件路径无效: {video_file_path}")
        
        # 创建或获取审核记录
        moderation, created = ModerationResult.objects.get_or_create(
            video_id=video_id,
            defaults={'status': 'processing'}
        )
        
        if not created:
            moderation.status = 'processing'
            moderation.error_message = ''
            moderation.save(update_fields=['status', 'error_message'])
        
        # 模型路径
        model_path = os.path.join(
            settings.BASE_DIR,
            'video',
            'models',
            'EVA-based_Fast_NSFW_Image_Classifier'
        )
        
        if not os.path.exists(model_path):
            raise ValueError(f"NSFW 模型不存在: {model_path}")
        
        # 创建保存问题帧的目录
        frames_dir = os.path.join(
            settings.MEDIA_ROOT,
            'ai_moderation',
            'flagged_frames',
            str(video_id)
        )
        Path(frames_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[Task {task_id}] 开始检测，参数: level={threshold_level}, threshold={threshold}, fps={fps}")
        logger.info(f"[Task {task_id}] 问题帧保存目录: {frames_dir}")
        
        # 执行检测（带进度回调）
        def progress_callback(current, total, flagged_frames):
            """进度回调函数"""
            progress = int((current / total) * 100) if total > 0 else 0
            
            # 更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': current,
                    'total': total,
                    'progress': progress,
                    'flagged_count': len(flagged_frames),
                    'flagged_frames': flagged_frames[-10:] if len(flagged_frames) > 10 else flagged_frames  # 只返回最新10个
                }
            )
            
            # 更新数据库记录（每10帧更新一次）
            if current % 10 == 0 or current == total:
                try:
                    moderation.details = {
                        'progress': progress,
                        'current_frame': current,
                        'total_frames': total,
                        'flagged_count': len(flagged_frames),
                        'threshold_level': threshold_level,
                        'threshold': threshold,
                        'fps': fps
                    }
                    moderation.flagged_frames = flagged_frames
                    moderation.save(update_fields=['details', 'flagged_frames'])
                except Exception as e:
                    logger.error(f"[Task {task_id}] 更新进度失败: {e}")
        
        result = detector.detect_video(
            video_path=video_file_path,
            model_path=model_path,
            threshold_level=threshold_level,
            threshold=threshold,
            fps=fps,
            batch_size=4,
            save_frames=True,
            frames_dir=frames_dir,
            progress_callback=progress_callback  # 传入进度回调
        )
        
        # 直接使用模型返回的累积概率
        max_scores = result['max_scores']
        
        # 直接使用模型输出，与 README 保持一致
        neutral_score = max_scores.get('neutral', 0.0)  # 正常内容
        low_score = max_scores.get('low', 0.0)          # 低风险及以上
        medium_score = max_scores.get('medium', 0.0)    # 中风险及以上
        high_score = max_scores.get('high', 0.0)        # 高风险
        
        # 判断审核结果和置信度
        if result['is_safe']:
            moderation_result = 'safe'
            confidence = neutral_score
        elif medium_score >= 0.7:
            moderation_result = 'unsafe'
            confidence = medium_score
        else:
            moderation_result = 'uncertain'
            confidence = medium_score
        
        # 更新审核记录
        moderation.status = 'completed'
        moderation.result = moderation_result
        moderation.confidence = confidence
        moderation.neutral_score = neutral_score
        moderation.low_score = low_score
        moderation.medium_score = medium_score
        moderation.high_score = high_score
        moderation.flagged_frames = result['flagged_frames']
        moderation.details = {
            'total_frames': result['total_frames'],
            'flagged_count': result['flagged_count'],
            'max_scores': result['max_scores'],
            'threshold_level': threshold_level,
            'threshold': threshold,
            'fps': fps,
            'frames_dir': f'ai_moderation/flagged_frames/{video_id}',
            'progress': 100
        }
        moderation.save()
        
        logger.info(f"[Task {task_id}] 审核完成: result={moderation_result}, confidence={confidence:.2f}")
        
        return {
            'video_id': video_id,
            'status': 'completed',
            'result': moderation_result,
            'confidence': confidence,
            'flagged_count': result['flagged_count']
        }
        
    except Video.DoesNotExist:
        logger.error(f"[Task {task_id}] 视频不存在: video_id={video_id}")
        return {'video_id': video_id, 'status': 'error', 'reason': 'video_not_found'}
    
    except Exception as e:
        logger.error(f"[Task {task_id}] 审核失败: {str(e)}", exc_info=True)
        
        if moderation:
            moderation.status = 'failed'
            moderation.error_message = str(e)
            moderation.save(update_fields=['status', 'error_message'])
        
        # 重试
        if self.request.retries < self.max_retries:
            logger.warning(f"[Task {task_id}] 将重试...")
            raise self.retry(exc=e)
        
        return {'video_id': video_id, 'status': 'error', 'reason': str(e)}
    
    finally:
        # 释放模型资源
        try:
            detector.release_model()
        except Exception:
            pass


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
def batch_moderate_videos(video_ids, threshold_level='medium', threshold=0.6, fps=1):
    """
    批量审核视频
    
    Args:
        video_ids: 视频 ID 列表
        threshold_level: 检测级别
        threshold: 置信度阈值
        fps: 每秒抽取帧数
    """
    results = []
    for video_id in video_ids:
        try:
            result = moderate_video_task.delay(video_id, threshold_level, threshold, fps)
            results.append({'video_id': video_id, 'task_id': result.id, 'status': 'submitted'})
        except Exception as e:
            logger.error(f"提交视频 {video_id} 审核任务失败: {str(e)}")
            results.append({'video_id': video_id, 'error': str(e), 'status': 'failed'})
    
    return results
