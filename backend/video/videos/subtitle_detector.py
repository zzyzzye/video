"""
字幕检测模块
使用 FFprobe 检测软字幕，使用 PaddleOCR 检测硬字幕
"""
import os
import json
import subprocess
import tempfile
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SubtitleDetector:
    """字幕检测器"""
    
    def __init__(self):
        """初始化检测器"""
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """延迟初始化 PaddleOCR（避免启动时加载）"""
        try:
            from paddleocr import PaddleOCR
            from django.conf import settings
            
            # 模型路径
            models_dir = os.path.join(settings.BASE_DIR, 'video', 'models')
            det_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_det')
            rec_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_rec')
            
            # 检查模型是否存在
            if not os.path.exists(det_model_dir) or not os.path.exists(rec_model_dir):
                logger.error(f"OCR models not found at {models_dir}")
                logger.error(f"Detection model exists: {os.path.exists(det_model_dir)}")
                logger.error(f"Recognition model exists: {os.path.exists(rec_model_dir)}")
                self.ocr = None
                return
            
            # 设置环境变量，禁用模型下载
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
            
            logger.info(f"Using local PP-OCRv5 models from: {models_dir}")
            
            # 使用本地模型路径（而不是模型名称）
            self.ocr = PaddleOCR(
                text_detection_model_dir=det_model_dir,
                text_recognition_model_dir=rec_model_dir,
                use_textline_orientation=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
            )
            
            logger.info("PaddleOCR initialized successfully with local models")
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}. Hard subtitle detection will be disabled.")
            self.ocr = None
    
    def detect_subtitle(self, video_path: str) -> Dict:
        """
        检测视频字幕
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            {
                'has_subtitle': bool,
                'subtitle_type': 'none' | 'soft' | 'hard',
                'subtitle_language': str,  # 如 'zh', 'en', 'zh,en'
                'details': dict  # 详细信息
            }
        """
        logger.info(f"Starting subtitle detection for: {video_path}")
        
        # 1. 先检测软字幕（快速）
        soft_result = self._detect_soft_subtitle(video_path)
        if soft_result['has_subtitle']:
            logger.info(f"Soft subtitle detected: {soft_result}")
            return {
                'has_subtitle': True,
                'subtitle_type': 'soft',
                'subtitle_language': soft_result.get('language', ''),
                'details': soft_result
            }
        
        # 2. 如果没有软字幕，检测硬字幕（较慢）
        if self.ocr:
            hard_result = self._detect_hard_subtitle(video_path)
            if hard_result['has_subtitle']:
                logger.info(f"Hard subtitle detected: {hard_result}")
                return {
                    'has_subtitle': True,
                    'subtitle_type': 'hard',
                    'subtitle_language': hard_result.get('language', ''),
                    'details': hard_result
                }
        else:
            logger.warning("PaddleOCR not available, skipping hard subtitle detection")
        
        # 3. 没有检测到字幕
        logger.info("No subtitle detected")
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
                'tracks': list,  # 字幕轨道列表
                'language': str
            }
        """
        try:
            # 使用 ffprobe 获取字幕流信息
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 's',  # 选择字幕流
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
                logger.error(f"FFprobe error: {result.stderr}")
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
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout for {video_path}")
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
        except Exception as e:
            logger.error(f"Error detecting soft subtitle: {e}")
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
    
    def _detect_hard_subtitle(self, video_path: str, sample_count: int = 10) -> Dict:
        """
        使用 PaddleOCR 检测硬字幕
        
        Args:
            video_path: 视频文件路径
            sample_count: 采样帧数（均匀分布在视频中）
            
        Returns:
            {
                'has_subtitle': bool,
                'detected_frames': int,  # 检测到字幕的帧数
                'total_frames': int,  # 总采样帧数
                'language': str
            }
        """
        if not self.ocr:
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
        
        try:
            # 1. 获取视频时长
            duration = self._get_video_duration(video_path)
            if duration <= 0:
                logger.error(f"Invalid video duration: {duration}")
                return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
            
            # 2. 计算采样时间点（均匀分布）
            sample_times = self._calculate_sample_times(duration, sample_count)
            logger.info(f"Sampling {sample_count} frames at times: {sample_times}")
            
            # 3. 提取帧并检测文字
            detected_count = 0
            has_chinese = False
            has_english = False
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, time_point in enumerate(sample_times):
                    frame_path = os.path.join(temp_dir, f'frame_{i}.jpg')
                    
                    # 提取帧（只提取底部 30% 区域，字幕通常在这里）
                    if self._extract_frame(video_path, time_point, frame_path):
                        # OCR 检测
                        if self._has_text_in_subtitle_area(frame_path):
                            detected_count += 1
                            # 简单判断语言（可以更复杂）
                            # 这里只是示例，实际可以分析 OCR 结果
                            has_chinese = True  # PaddleOCR 默认是中文
            
            # 4. 判断是否有字幕（阈值：至少 30% 的帧检测到文字，最少2帧）
            threshold = max(2, sample_count * 0.3)
            has_subtitle = detected_count >= threshold
            
            # 5. 判断语言
            language = ''
            if has_subtitle:
                if has_chinese:
                    language = 'zh'
                if has_english:
                    language = 'en' if not language else f'{language},en'
            
            logger.info(f"Hard subtitle detection: {detected_count}/{sample_count} frames, has_subtitle={has_subtitle}")
            
            return {
                'has_subtitle': has_subtitle,
                'detected_frames': detected_count,
                'total_frames': sample_count,
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Error detecting hard subtitle: {e}", exc_info=True)
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
    
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
                duration = float(data.get('format', {}).get('duration', 0))
                return duration
            
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
        
        return 0
    
    def _calculate_sample_times(self, duration: float, count: int) -> List[float]:
        """
        计算均匀分布的采样时间点
        
        Args:
            duration: 视频时长（秒）
            count: 采样数量
            
        Returns:
            采样时间点列表
        """
        if count <= 1:
            return [duration / 2]
        
        # 均匀分布：0%, 11%, 22%, ..., 100%
        times = []
        for i in range(count):
            percentage = i / (count - 1)  # 0.0 到 1.0
            time_point = duration * percentage
            # 避免取到最后一帧（可能是黑屏）
            if time_point >= duration:
                time_point = duration - 1
            times.append(round(time_point, 2))
        
        return times
    
    def _extract_frame(self, video_path: str, time_point: float, output_path: str) -> bool:
        """
        使用 FFmpeg 提取指定时间点的帧
        
        Args:
            video_path: 视频路径
            time_point: 时间点（秒）
            output_path: 输出图片路径
            
        Returns:
            是否成功
        """
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(time_point),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',  # 质量
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"Error extracting frame at {time_point}s: {e}")
            return False
    
    def _has_text_in_subtitle_area(self, image_path: str) -> bool:
        """
        检测图片底部区域是否有文字（字幕区域）
        
        Args:
            image_path: 图片路径
            
        Returns:
            是否检测到文字
        """
        try:
            # 使用 PaddleOCR 3.x 检测
            result = self.ocr.predict(image_path)
            
            if not result or len(result) == 0:
                return False
            
            # 加载图片获取尺寸
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # 定义字幕区域（底部 30%）
            subtitle_area_top = img_height * 0.7
            
            # 检查是否有文字在字幕区域
            text_count = 0
            for page_result in result:
                # 尝试通过 json 属性获取结果
                if hasattr(page_result, 'json'):
                    json_data = page_result.json
                    if isinstance(json_data, dict) and 'res' in json_data:
                        res = json_data['res']
                        if isinstance(res, dict) and 'rec_texts' in res and 'rec_boxes' in res:
                            rec_texts = res['rec_texts']
                            rec_boxes = res['rec_boxes']
                            
                            for idx, (text, box) in enumerate(zip(rec_texts, rec_boxes)):
                                if not text or not box:
                                    continue
                                
                                # box 格式: [x1, y1, x2, y2]
                                x1, y1, x2, y2 = box
                                center_y = (y1 + y2) / 2
                                
                                # 判断是否在字幕区域
                                if center_y >= subtitle_area_top:
                                    text_count += 1
                                    # 如果检测到文字，可以提前返回
                                    if text_count >= 1:
                                        return True
            
            return text_count > 0
            
        except Exception as e:
            logger.error(f"Error in OCR detection: {e}")
            return False


# 单例模式
_detector_instance = None

def get_subtitle_detector() -> SubtitleDetector:
    """获取字幕检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SubtitleDetector()
    return _detector_instance
