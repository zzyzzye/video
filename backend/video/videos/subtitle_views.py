"""
字幕相关视图
"""
import asyncio
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Video
from ai_service.services.deepseek_service import DeepSeekService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_subtitles(request, video_id):
    """
    翻译视频字幕
    
    请求参数:
    - target_language: 目标语言 (zh/en/ja 等)
    """
    return asyncio.run(_translate_subtitles_async(request, video_id))


async def _translate_subtitles_async(request, video_id):
    try:
        video = await asyncio.to_thread(get_object_or_404, Video, id=video_id, user=request.user)
        target_language = request.data.get('target_language', 'en')
        
        # 获取字幕草稿
        subtitles = video.subtitles_draft
        if not subtitles or len(subtitles) == 0:
            return Response(
                {'error': '视频暂无字幕'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 语言映射
        language_map = {
            'zh': '中文',
            'en': '英文',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'ru': '俄语',
        }
        target_lang_name = language_map.get(target_language, '英文')
        
        # 初始化 DeepSeek 服务
        deepseek_service = DeepSeekService()
        
        # 批量翻译字幕（每次翻译10条，避免单次请求过大）
        batch_size = 10
        translated_subtitles = []
        
        # 准备任务列表
        tasks = []
        batches = []
        
        for i in range(0, len(subtitles), batch_size):
            batch = subtitles[i:i + batch_size]
            batches.append(batch)
            
            # 构建批量翻译文本
            texts_to_translate = []
            for idx, subtitle in enumerate(batch):
                text = subtitle.get('text', '')
                if text:
                    texts_to_translate.append(f"{idx + 1}. {text}")
            
            if not texts_to_translate:
                tasks.append(asyncio.sleep(0, result=None)) # 占位
                continue
            
            # 调用 DeepSeek 翻译
            combined_text = '\n'.join(texts_to_translate)
            messages = [
                {
                    "role": "system",
                    "content": f"你是一个专业的字幕翻译助手。请将以下字幕翻译成{target_lang_name}。保持编号格式，每行一条翻译结果。翻译要准确、自然、符合目标语言习惯。"
                },
                {
                    "role": "user",
                    "content": f"请翻译以下字幕：\n\n{combined_text}"
                }
            ]
            tasks.append(deepseek_service.chat_completion(messages, temperature=0.3))

        # 并发执行所有翻译任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for batch, result in zip(batches, results):
            if result is None or isinstance(result, Exception):
                if isinstance(result, Exception):
                    logger.error(f"翻译字幕批次失败: {str(result)}")
                # 失败时保留原文
                for subtitle in batch:
                    new_subtitle = subtitle.copy()
                    new_subtitle['translation'] = subtitle.get('text', '')
                    translated_subtitles.append(new_subtitle)
                continue

            try:
                translated_text = result['choices'][0]['message']['content']
                # 解析翻译结果
                translated_lines = translated_text.strip().split('\n')
                translated_dict = {}
                
                for line in translated_lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0].strip()) - 1
                            translation = parts[1].strip()
                            translated_dict[idx] = translation
                        except ValueError:
                            continue
                
                # 将翻译结果填充到字幕中
                for idx, subtitle in enumerate(batch):
                    new_subtitle = subtitle.copy()
                    if idx in translated_dict:
                        new_subtitle['translation'] = translated_dict[idx]
                    else:
                        new_subtitle['translation'] = subtitle.get('text', '')
                    translated_subtitles.append(new_subtitle)
            except Exception as e:
                logger.error(f"解析翻译结果失败: {str(e)}")
                for subtitle in batch:
                    new_subtitle = subtitle.copy()
                    new_subtitle['translation'] = subtitle.get('text', '')
                    translated_subtitles.append(new_subtitle)
        
        # 更新视频字幕草稿
        video.subtitles_draft = translated_subtitles
        await asyncio.to_thread(video.save, update_fields=['subtitles_draft'])
        
        return Response({
            'message': '字幕翻译成功',
            'subtitles': translated_subtitles
        })
        
    except Exception as e:
        logger.error(f"翻译字幕失败: {str(e)}")
        return Response(
            {'error': f'翻译失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_subtitles(request, video_id):
    """
    优化视频字幕（修正错别字、标点符号等）
    """
    return asyncio.run(_optimize_subtitles_async(request, video_id))


async def _optimize_subtitles_async(request, video_id):
    try:
        video = await asyncio.to_thread(get_object_or_404, Video, id=video_id, user=request.user)
        
        # 获取字幕草稿
        subtitles = video.subtitles_draft
        if not subtitles or len(subtitles) == 0:
            return Response(
                {'error': '视频暂无字幕'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 初始化 DeepSeek 服务
        deepseek_service = DeepSeekService()
        
        # 批量优化字幕
        batch_size = 10
        optimized_subtitles = []
        
        tasks = []
        batches = []
        
        for i in range(0, len(subtitles), batch_size):
            batch = subtitles[i:i + batch_size]
            batches.append(batch)
            
            # 构建批量优化文本
            texts_to_optimize = []
            for idx, subtitle in enumerate(batch):
                text = subtitle.get('text', '')
                if text:
                    texts_to_optimize.append(f"{idx + 1}. {text}")
            
            if not texts_to_optimize:
                tasks.append(asyncio.sleep(0, result=None))
                continue
            
            # 调用 DeepSeek 优化
            combined_text = '\n'.join(texts_to_optimize)
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的字幕优化助手。请优化字幕文本，修正错别字、标点符号，使其更加通顺易读。保持编号格式，每行一条优化结果。保持原意不变。"
                },
                {
                    "role": "user",
                    "content": f"请优化以下字幕：\n\n{combined_text}"
                }
            ]
            tasks.append(deepseek_service.chat_completion(messages, temperature=0.3))

        # 并发执行所有优化任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for batch, result in zip(batches, results):
            if result is None or isinstance(result, Exception):
                if isinstance(result, Exception):
                    logger.error(f"优化字幕批次失败: {str(result)}")
                optimized_subtitles.extend(batch)
                continue

            try:
                optimized_text = result['choices'][0]['message']['content']
                # 解析优化结果
                optimized_lines = optimized_text.strip().split('\n')
                optimized_dict = {}
                
                for line in optimized_lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0].strip()) - 1
                            optimized = parts[1].strip()
                            optimized_dict[idx] = optimized
                        except ValueError:
                            continue
                
                # 将优化结果填充到字幕中
                for idx, subtitle in enumerate(batch):
                    new_subtitle = subtitle.copy()
                    if idx in optimized_dict:
                        new_subtitle['text'] = optimized_dict[idx]
                    optimized_subtitles.append(new_subtitle)
            except Exception as e:
                logger.error(f"解析优化结果失败: {str(e)}")
                optimized_subtitles.extend(batch)
        
        # 更新视频字幕草稿
        video.subtitles_draft = optimized_subtitles
        await asyncio.to_thread(video.save, update_fields=['subtitles_draft'])
        
        return Response({
            'message': '字幕优化成功',
            'subtitles': optimized_subtitles
        })
        
    except Exception as e:
        logger.error(f"优化字幕失败: {str(e)}")
        return Response(
            {'error': f'优化失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
