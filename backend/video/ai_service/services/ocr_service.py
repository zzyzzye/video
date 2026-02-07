"""
OCR 字幕检测服务
使用 PaddleOCR 检测视频中的硬字幕
"""
import os
import json
import subprocess
import tempfile
from typing import Dict, List
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """OCR 字幕检测服务"""
    
    def __init__(self):
        self.ocr = None
        self.models_dir = self._get_models_dir()
    
    def _get_models_dir(self):
        """获取 OCR 模型目录"""
        return Path(settings.BASE_DIR) / 'video' / 'models'
    
    def _load_ocr(self):
        """加载 PaddleOCR 模型"""
        if self.ocr is not None:
            return self.ocr
        
        logger.info("开始加载 PaddleOCR")
        
        try:
            from paddleocr import PaddleOCR
            import gc
            
            # 设置环境变量，禁用模型下载检查
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
            
            # 模型路径
            det_model_dir = self.models_dir / 'PP-OCRv5_server_det'
            rec_model_dir = self.models_dir / 'PP-OCRv5_server_rec'
            
            logger.info(f"检测模型路径: {det_model_dir}")
            logger.info(f"识别模型路径: {rec_model_dir}")
            
            # 检查模型是否存在
            if not det_model_dir.exists() or not rec_model_dir.exists():
                logger.error(f"OCR 模型未找到")
                logger.error(f"检测模型存在: {det_model_dir.exists()}")
                logger.error(f"识别模型存在: {rec_model_dir.exists()}")
                return None
            
            # 使用本地模型路径
            self.ocr = PaddleOCR(
                text_detection_model_dir=str(det_model_dir),
                text_recognition_model_dir=str(rec_model_dir),
                use_textline_orientation=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_gpu=True  # 启用 GPU 加速
            )
            
            logger.info("PaddleOCR 加载成功")
            return self.ocr
            
        except Exception as e:
            logger.error(f"PaddleOCR 加载失败: {e}", exc_info=True)
            return None
    
    def detect_subtitle(self, video_path: str) -> Dict:
        """
        检测视频字幕（软字幕 + 硬字幕）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            {
                'has_subtitle': bool,
                'subtitle_type': 'none' | 'soft' | 'hard',
                'subtitle_language': str,
                'details': dict
            }
        """
        logger.info(f"开始字幕检测: {video_path}")
        
        # 1. 先检测软字幕（快速）
        logger.info("检测软字幕...")
        soft_result = self._detect_soft_subtitle(video_path)
        
        if soft_result['has_subtitle']:
            logger.info(f"检测到软字幕: {soft_result}")
            return {
                'has_subtitle': True,
                'subtitle_type': 'soft',
                'subtitle_language': soft_result.get('language', ''),
                'details': soft_result
            }
        
        logger.info("未检测到软字幕")
        
        # 2. 检测硬字幕（较慢）
        logger.info("检测硬字幕...")
        hard_result = self._detect_hard_subtitle(video_path)
        
        if hard_result['has_subtitle']:
            logger.info(f"检测到硬字幕: {hard_result}")
            return {
                'has_subtitle': True,
                'subtitle_type': 'hard',
                'subtitle_language': hard_result.get('language', ''),
                'details': hard_result
            }
        
        logger.info("未检测到硬字幕")
        
        # 3. 没有字幕
        logger.info("未检测到任何字幕")
        return {
            'has_subtitle': False,
            'subtitle_type': 'none',
            'subtitle_language': '',
            'details': {}
        }
    
    def _detect_soft_subtitle(self, video_path: str) -> Dict:
        """
        使用 FFprobe 检测软字幕
        
        Returns:
            {
                'has_subtitle': bool,
                'tracks': list,
                'language': str
            }
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index,codec_name,codec_type:stream_tags=language',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"FFprobe 错误: {result.stderr}")
                return {'has_subtitle': False, 'tracks': [], 'language': ''}
            
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            
            if not streams:
                return {'has_subtitle': False, 'tracks': [], 'language': ''}
            
            # 提取字幕轨道信息
            tracks = []
            languages = set()
            
            for stream in streams:
                track_info = {
                    'index': stream.get('index'),
                    'codec': stream.get('codec_name'),
                    'language': stream.get('tags', {}).get('language', 'unknown')
                }
                tracks.append(track_info)
                
                lang = track_info['language']
                if lang and lang != 'unknown':
                    languages.add(lang)
            
            return {
                'has_subtitle': True,
                'tracks': tracks,
                'language': ','.join(sorted(languages)) if languages else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"软字幕检测失败: {e}", exc_info=True)
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
    
    def _detect_hard_subtitle(self, video_path: str, sample_count: int = 10) -> Dict:
        """
        使用 PaddleOCR 检测硬字幕
        
        Args:
            video_path: 视频文件路径
            sample_count: 采样帧数
            
        Returns:
            {
                'has_subtitle': bool,
                'detected_frames': int,
                'total_frames': int,
                'language': str
            }
        """
        # 加载 OCR
        ocr = self._load_ocr()
        if not ocr:
            logger.warning("OCR 不可用，无法检测硬字幕")
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
        
        try:
            # 获取视频时长
            duration = self._get_video_duration(video_path)
            if duration <= 0:
                logger.error(f"无效的视频时长: {duration}")
                return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
            
            # 计算采样时间点
            sample_times = self._calculate_sample_times(duration, sample_count)
            logger.info(f"采样 {sample_count} 帧，时间点: {sample_times}")
            
            # 提取帧并检测
            detected_count = 0
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, time_point in enumerate(sample_times):
                    frame_path = os.path.join(temp_dir, f'frame_{i}.jpg')
                    
                    if self._extract_frame(video_path, time_point, frame_path):
                        if self._has_text_in_subtitle_area(frame_path, ocr):
                            detected_count += 1
                            logger.info(f"第 {i+1} 帧检测到字幕")
            
            # 判断是否有字幕（阈值：至少 30% 的帧，最少2帧）
            threshold = max(2, sample_count * 0.3)
            has_subtitle = detected_count >= threshold
            
            logger.info(f"硬字幕检测: {detected_count}/{sample_count} 帧，阈值: {threshold}，结果: {has_subtitle}")
            
            return {
                'has_subtitle': has_subtitle,
                'detected_frames': detected_count,
                'total_frames': sample_count,
                'language': 'zh' if has_subtitle else ''
            }
            
        except Exception as e:
            logger.error(f"硬字幕检测失败: {e}", exc_info=True)
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
        finally:
            # 释放 OCR 内存
            if ocr:
                del ocr
                import gc
                gc.collect()
                logger.info("OCR 模型已释放")
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
            
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
        
        return 0
    
    def _calculate_sample_times(self, duration: float, count: int) -> List[float]:
        """计算均匀分布的采样时间点"""
        if count <= 1:
            return [duration / 2]
        
        times = []
        for i in range(count):
            percentage = i / (count - 1)
            time_point = duration * percentage
            if time_point >= duration:
                time_point = duration - 1
            times.append(round(time_point, 2))
        
        return times
    
    def _extract_frame(self, video_path: str, time_point: float, output_path: str) -> bool:
        """提取指定时间点的帧"""
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(time_point),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"提取帧失败: {e}")
            return False
    
    def _has_text_in_subtitle_area(self, image_path: str, ocr) -> bool:
        """检测图片底部区域是否有文字"""
        try:
            result = ocr.predict(image_path)
            
            if not result or len(result) == 0:
                return False
            
            # 加载图片获取尺寸
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # 字幕区域（底部 30%）
            subtitle_area_top = img_height * 0.7
            
            # 检查是否有文字在字幕区域
            for page_result in result:
                if hasattr(page_result, 'json'):
                    json_data = page_result.json
                    
                    if isinstance(json_data, dict) and 'res' in json_data:
                        res = json_data['res']
                        if isinstance(res, dict) and 'rec_texts' in res and 'rec_boxes' in res:
                            rec_texts = res['rec_texts']
                            rec_boxes = res['rec_boxes']
                            
                            for text, box in zip(rec_texts, rec_boxes):
                                if not text or not box:
                                    continue
                                
                                # box 格式: [x1, y1, x2, y2]
                                x1, y1, x2, y2 = box
                                center_y = (y1 + y2) / 2
                                
                                # 判断是否在字幕区域
                                if center_y >= subtitle_area_top:
                                    logger.info(f"在字幕区域检测到文字: '{text}'")
                                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"OCR 检测失败: {e}", exc_info=True)
            return False
    
    def release_model(self):
        """释放 OCR 模型内存"""
        if self.ocr is not None:
            del self.ocr
            self.ocr = None
            
            import gc
            gc.collect()
            logger.info("OCR 模型已释放")
