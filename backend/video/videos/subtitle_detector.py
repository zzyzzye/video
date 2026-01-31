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
from datetime import datetime

# 创建专门的字幕检测日志记录器
subtitle_logger = logging.getLogger('subtitle_detector')
subtitle_logger.setLevel(logging.DEBUG)

# 如果还没有处理器，添加文件处理器
if not subtitle_logger.handlers:
    from django.conf import settings
    
    # 日志文件路径
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'subtitle_detection.log')
    
    # 文件处理器 - 详细的 DEBUG 级别日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 格式化器 - 包含更多信息
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    subtitle_logger.addHandler(file_handler)
    subtitle_logger.info("=" * 80)
    subtitle_logger.info("字幕检测日志系统初始化完成")
    subtitle_logger.info("=" * 80)

# 保留原有的 logger 用于一般日志
logger = logging.getLogger(__name__)


class SubtitleDetector:
    """字幕检测器"""
    
    def __init__(self):
        """初始化检测器"""
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """延迟初始化 PaddleOCR（避免启动时加载）"""
        subtitle_logger.info("开始初始化 PaddleOCR")
        try:
            from paddleocr import PaddleOCR
            from django.conf import settings
            
            # 设置环境变量，禁用模型下载检查（必须在导入前设置）
            os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
            subtitle_logger.debug("设置环境变量: DISABLE_MODEL_SOURCE_CHECK=True")
            
            # 模型路径
            models_dir = os.path.join(settings.BASE_DIR, 'video', 'models')
            det_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_det')
            rec_model_dir = os.path.join(models_dir, 'PP-OCRv5_server_rec')
            
            subtitle_logger.debug(f"模型目录: {models_dir}")
            subtitle_logger.debug(f"检测模型路径: {det_model_dir}")
            subtitle_logger.debug(f"识别模型路径: {rec_model_dir}")
            
            # 检查模型是否存在
            det_exists = os.path.exists(det_model_dir)
            rec_exists = os.path.exists(rec_model_dir)
            
            subtitle_logger.debug(f"检测模型存在: {det_exists}")
            subtitle_logger.debug(f"识别模型存在: {rec_exists}")
            
            if not det_exists or not rec_exists:
                subtitle_logger.error(f"OCR 模型未找到，路径: {models_dir}")
                subtitle_logger.error(f"检测模型存在: {det_exists}")
                subtitle_logger.error(f"识别模型存在: {rec_exists}")
                self.ocr = None
                return
            
            subtitle_logger.info(f"使用本地模型初始化 PaddleOCR: {models_dir}")
            
            # 使用本地模型路径（而不是模型名称）
            # 注意：PaddleOCR 3.x 版本已移除 show_log 参数
            self.ocr = PaddleOCR(
                text_detection_model_dir=det_model_dir,
                text_recognition_model_dir=rec_model_dir,
                use_textline_orientation=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_gpu=True  # 启用 GPU 加速
            )
            
            subtitle_logger.info("PaddleOCR 初始化成功")
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            subtitle_logger.error(f"PaddleOCR 初始化失败: {e}", exc_info=True)
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
        subtitle_logger.info("=" * 80)
        subtitle_logger.info(f"开始字幕检测")
        subtitle_logger.info(f"视频路径: {video_path}")
        subtitle_logger.debug(f"视频文件存在: {os.path.exists(video_path)}")
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            subtitle_logger.debug(f"视频文件大小: {file_size / (1024*1024):.2f} MB")
        
        logger.info(f"Starting subtitle detection for: {video_path}")
        
        # 1. 先检测软字幕（快速）
        subtitle_logger.info("步骤 1: 检测软字幕")
        soft_result = self._detect_soft_subtitle(video_path)
        subtitle_logger.debug(f"软字幕检测结果: {soft_result}")
        
        if soft_result['has_subtitle']:
            subtitle_logger.info(f"✓ 检测到软字幕: {soft_result}")
            logger.info(f"Soft subtitle detected: {soft_result}")
            result = {
                'has_subtitle': True,
                'subtitle_type': 'soft',
                'subtitle_language': soft_result.get('language', ''),
                'details': soft_result
            }
            subtitle_logger.info(f"最终结果: {result}")
            subtitle_logger.info("=" * 80)
            return result
        
        subtitle_logger.info("✗ 未检测到软字幕")
        
        # 2. 如果没有软字幕，检测硬字幕（较慢）
        subtitle_logger.info("步骤 2: 检测硬字幕")
        subtitle_logger.debug(f"OCR 可用: {self.ocr is not None}")
        
        if self.ocr:
            hard_result = self._detect_hard_subtitle(video_path)
            subtitle_logger.debug(f"硬字幕检测结果: {hard_result}")
            
            if hard_result['has_subtitle']:
                subtitle_logger.info(f"✓ 检测到硬字幕: {hard_result}")
                logger.info(f"Hard subtitle detected: {hard_result}")
                result = {
                    'has_subtitle': True,
                    'subtitle_type': 'hard',
                    'subtitle_language': hard_result.get('language', ''),
                    'details': hard_result
                }
                subtitle_logger.info(f"最终结果: {result}")
                subtitle_logger.info("=" * 80)
                return result
            
            subtitle_logger.info("✗ 未检测到硬字幕")
        else:
            subtitle_logger.warning("PaddleOCR 不可用，跳过硬字幕检测")
            logger.warning("PaddleOCR not available, skipping hard subtitle detection")
        
        # 3. 没有检测到字幕
        subtitle_logger.info("✗ 未检测到任何字幕")
        logger.info("No subtitle detected")
        result = {
            'has_subtitle': False,
            'subtitle_type': 'none',
            'subtitle_language': '',
            'details': {}
        }
        subtitle_logger.info(f"最终结果: {result}")
        subtitle_logger.info("=" * 80)
        return result
    
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
        subtitle_logger.debug("开始软字幕检测")
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
            
            subtitle_logger.debug(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            subtitle_logger.debug(f"FFprobe 返回码: {result.returncode}")
            
            if result.returncode != 0:
                subtitle_logger.error(f"FFprobe 错误: {result.stderr}")
                logger.error(f"FFprobe error: {result.stderr}")
                return {'has_subtitle': False, 'tracks': [], 'language': ''}
            
            subtitle_logger.debug(f"FFprobe 输出: {result.stdout[:500]}")  # 只记录前500字符
            
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            
            subtitle_logger.debug(f"找到 {len(streams)} 个字幕流")
            
            if not streams:
                subtitle_logger.debug("没有找到字幕流")
                return {'has_subtitle': False, 'tracks': [], 'language': ''}
            
            # 提取字幕轨道信息
            tracks = []
            languages = set()
            
            for idx, stream in enumerate(streams):
                track_info = {
                    'index': stream.get('index'),
                    'codec': stream.get('codec_name'),
                    'language': stream.get('tags', {}).get('language', 'unknown')
                }
                tracks.append(track_info)
                subtitle_logger.debug(f"字幕轨道 {idx + 1}: {track_info}")
                
                lang = track_info['language']
                if lang and lang != 'unknown':
                    languages.add(lang)
            
            result_data = {
                'has_subtitle': True,
                'tracks': tracks,
                'language': ','.join(sorted(languages)) if languages else 'unknown'
            }
            subtitle_logger.info(f"软字幕检测成功: {len(tracks)} 个轨道, 语言: {result_data['language']}")
            return result_data
            
        except subprocess.TimeoutExpired:
            subtitle_logger.error(f"FFprobe 超时: {video_path}")
            logger.error(f"FFprobe timeout for {video_path}")
            return {'has_subtitle': False, 'tracks': [], 'language': ''}
        except Exception as e:
            subtitle_logger.error(f"软字幕检测异常: {e}", exc_info=True)
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
        subtitle_logger.debug("开始硬字幕检测")
        
        if not self.ocr:
            subtitle_logger.warning("OCR 未初始化，无法检测硬字幕")
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
        
        try:
            # 1. 获取视频时长
            subtitle_logger.debug("获取视频时长")
            duration = self._get_video_duration(video_path)
            subtitle_logger.debug(f"视频时长: {duration} 秒")
            
            if duration <= 0:
                subtitle_logger.error(f"无效的视频时长: {duration}")
                logger.error(f"Invalid video duration: {duration}")
                return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
            
            # 2. 计算采样时间点（均匀分布）
            sample_times = self._calculate_sample_times(duration, sample_count)
            subtitle_logger.info(f"采样 {sample_count} 帧，时间点: {sample_times}")
            logger.info(f"Sampling {sample_count} frames at times: {sample_times}")
            
            # 3. 提取帧并检测文字
            detected_count = 0
            has_chinese = False
            has_english = False
            
            with tempfile.TemporaryDirectory() as temp_dir:
                subtitle_logger.debug(f"临时目录: {temp_dir}")
                
                for i, time_point in enumerate(sample_times):
                    frame_path = os.path.join(temp_dir, f'frame_{i}.jpg')
                    subtitle_logger.debug(f"处理第 {i+1}/{sample_count} 帧，时间点: {time_point}s")
                    
                    # 提取帧（只提取底部 30% 区域，字幕通常在这里）
                    if self._extract_frame(video_path, time_point, frame_path):
                        subtitle_logger.debug(f"帧提取成功: {frame_path}")
                        
                        # OCR 检测
                        has_text = self._has_text_in_subtitle_area(frame_path)
                        subtitle_logger.debug(f"OCR 检测结果: {has_text}")
                        
                        if has_text:
                            detected_count += 1
                            subtitle_logger.info(f"✓ 第 {i+1} 帧检测到字幕文字")
                            # 简单判断语言（可以更复杂）
                            # 这里只是示例，实际可以分析 OCR 结果
                            has_chinese = True  # PaddleOCR 默认是中文
                        else:
                            subtitle_logger.debug(f"✗ 第 {i+1} 帧未检测到字幕文字")
                    else:
                        subtitle_logger.warning(f"第 {i+1} 帧提取失败")
            
            # 4. 判断是否有字幕（阈值：至少 30% 的帧检测到文字，最少2帧）
            threshold = max(2, sample_count * 0.3)
            has_subtitle = detected_count >= threshold
            
            subtitle_logger.info(f"检测统计: {detected_count}/{sample_count} 帧有字幕，阈值: {threshold}")
            subtitle_logger.info(f"判定结果: {'有硬字幕' if has_subtitle else '无硬字幕'}")
            
            # 5. 判断语言
            language = ''
            if has_subtitle:
                if has_chinese:
                    language = 'zh'
                if has_english:
                    language = 'en' if not language else f'{language},en'
                subtitle_logger.debug(f"检测到的语言: {language}")
            
            logger.info(f"Hard subtitle detection: {detected_count}/{sample_count} frames, has_subtitle={has_subtitle}")
            
            return {
                'has_subtitle': has_subtitle,
                'detected_frames': detected_count,
                'total_frames': sample_count,
                'language': language
            }
            
        except Exception as e:
            subtitle_logger.error(f"硬字幕检测异常: {e}", exc_info=True)
            logger.error(f"Error detecting hard subtitle: {e}", exc_info=True)
            return {'has_subtitle': False, 'detected_frames': 0, 'total_frames': 0, 'language': ''}
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        subtitle_logger.debug(f"获取视频时长: {video_path}")
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            
            subtitle_logger.debug(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            subtitle_logger.debug(f"FFprobe 返回码: {result.returncode}")
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data.get('format', {}).get('duration', 0))
                subtitle_logger.debug(f"视频时长: {duration} 秒")
                return duration
            else:
                subtitle_logger.error(f"FFprobe 错误: {result.stderr}")
            
        except Exception as e:
            subtitle_logger.error(f"获取视频时长异常: {e}", exc_info=True)
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
        subtitle_logger.debug(f"计算采样时间点: 时长={duration}s, 数量={count}")
        
        if count <= 1:
            result = [duration / 2]
            subtitle_logger.debug(f"采样点: {result}")
            return result
        
        # 均匀分布：0%, 11%, 22%, ..., 100%
        times = []
        for i in range(count):
            percentage = i / (count - 1)  # 0.0 到 1.0
            time_point = duration * percentage
            # 避免取到最后一帧（可能是黑屏）
            if time_point >= duration:
                time_point = duration - 1
            times.append(round(time_point, 2))
        
        subtitle_logger.debug(f"采样点: {times}")
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
        subtitle_logger.debug(f"提取帧: 时间点={time_point}s, 输出={output_path}")
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
            
            subtitle_logger.debug(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            
            success = result.returncode == 0 and os.path.exists(output_path)
            subtitle_logger.debug(f"FFmpeg 返回码: {result.returncode}, 文件存在: {os.path.exists(output_path)}")
            
            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                subtitle_logger.debug(f"提取的帧大小: {file_size / 1024:.2f} KB")
            
            if not success and result.stderr:
                subtitle_logger.error(f"FFmpeg 错误: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            
            return success
            
        except subprocess.TimeoutExpired:
            subtitle_logger.error(f"FFmpeg 超时: 时间点={time_point}s")
            return False
        except Exception as e:
            subtitle_logger.error(f"提取帧异常: {e}", exc_info=True)
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
        subtitle_logger.debug(f"OCR 检测图片: {image_path}")
        try:
            # 使用 PaddleOCR 3.x 检测
            subtitle_logger.debug("调用 PaddleOCR.predict()")
            result = self.ocr.predict(image_path)
            
            subtitle_logger.debug(f"OCR 结果类型: {type(result)}, 长度: {len(result) if result else 0}")
            
            if not result or len(result) == 0:
                subtitle_logger.debug("OCR 未返回结果")
                return False
            
            # 加载图片获取尺寸
            from PIL import Image
            img = Image.open(image_path)
            img_width, img_height = img.size
            subtitle_logger.debug(f"图片尺寸: {img_width}x{img_height}")
            
            # 定义字幕区域（底部 30%）
            subtitle_area_top = img_height * 0.7
            subtitle_logger.debug(f"字幕区域: Y >= {subtitle_area_top}")
            
            # 检查是否有文字在字幕区域
            text_count = 0
            total_text_count = 0
            
            for page_idx, page_result in enumerate(result):
                subtitle_logger.debug(f"处理第 {page_idx + 1} 页结果")
                
                # 尝试通过 json 属性获取结果
                if hasattr(page_result, 'json'):
                    json_data = page_result.json
                    subtitle_logger.debug(f"JSON 数据类型: {type(json_data)}")
                    
                    if isinstance(json_data, dict) and 'res' in json_data:
                        res = json_data['res']
                        if isinstance(res, dict) and 'rec_texts' in res and 'rec_boxes' in res:
                            rec_texts = res['rec_texts']
                            rec_boxes = res['rec_boxes']
                            
                            subtitle_logger.debug(f"检测到 {len(rec_texts)} 个文本框")
                            
                            for idx, (text, box) in enumerate(zip(rec_texts, rec_boxes)):
                                if not text or not box:
                                    continue
                                
                                total_text_count += 1
                                
                                # box 格式: [x1, y1, x2, y2]
                                x1, y1, x2, y2 = box
                                center_y = (y1 + y2) / 2
                                
                                subtitle_logger.debug(f"文本 {idx + 1}: '{text}', 位置: Y={center_y:.1f}, 框: {box}")
                                
                                # 判断是否在字幕区域
                                if center_y >= subtitle_area_top:
                                    text_count += 1
                                    subtitle_logger.info(f"✓ 在字幕区域检测到文字: '{text}' at Y={center_y:.1f}")
                                    # 如果检测到文字，可以提前返回
                                    if text_count >= 1:
                                        subtitle_logger.info(f"检测到字幕文字，提前返回")
                                        return True
                                else:
                                    subtitle_logger.debug(f"✗ 文字不在字幕区域: '{text}' at Y={center_y:.1f}")
            
            subtitle_logger.info(f"OCR 统计: 总文本={total_text_count}, 字幕区域文本={text_count}")
            return text_count > 0
            
        except Exception as e:
            subtitle_logger.error(f"OCR 检测异常: {e}", exc_info=True)
            logger.error(f"Error in OCR detection: {e}")
            return False


# 单例模式
_detector_instance = None

def get_subtitle_detector() -> SubtitleDetector:
    """获取字幕检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        subtitle_logger.info("创建字幕检测器单例")
        _detector_instance = SubtitleDetector()
    return _detector_instance
