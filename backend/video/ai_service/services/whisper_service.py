"""
Whisper 字幕生成服务
使用 faster-whisper 进行语音识别和字幕生成
"""
import os
import subprocess
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WhisperService:
    """Whisper 字幕生成服务"""
    
    def __init__(self):
        self.model = None
        self.model_dir = self._get_model_dir()
        self.device = None
        self.compute_type = None
    
    def _get_model_dir(self):
        """获取 Whisper 模型目录"""
        return Path(settings.BASE_DIR) / 'video' / 'models' / 'whisper-ct2-large-v3'
    
    def _load_model(self):
        """加载 Whisper 模型"""
        if self.model is not None:
            return self.model
        
        try:
            import torch
            from faster_whisper import WhisperModel
        except ImportError as e:
            logger.error(f"Whisper 依赖不可用: {e}")
            raise RuntimeError("Whisper 依赖未安装")
        
        # 检查模型目录
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Whisper 模型不存在: {self.model_dir}")
        
        # 确定设备和计算类型
        if torch.cuda.is_available():
            self.device = 'cuda'
            self.compute_type = 'int8_float16'
            logger.info("使用 CUDA 加速")
        else:
            self.device = 'cpu'
            self.compute_type = 'int8'
            logger.info("使用 CPU 推理")
        
        # 加载模型
        logger.info(f"加载 Whisper 模型: {self.model_dir}")
        self.model = WhisperModel(
            str(self.model_dir),
            device=self.device,
            compute_type=self.compute_type,
            num_workers=4
        )
        logger.info("Whisper 模型加载完成")
        
        return self.model
    
    def extract_audio(self, video_path, output_path):
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径
        """
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-map', '0:a:0',
            '-vn',
            '-ac', '1',
            '-ar', '16000',
            '-acodec', 'pcm_s16le',
            '-af', 'aresample=16000:resampler=soxr:precision=28,volume=0.95',
            '-y',
            str(output_path)
        ]
        
        logger.info(f"提取音频: {video_path} -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            error_msg = result.stderr or 'ffmpeg 提取音频失败'
            logger.error(f"音频提取失败: {error_msg}")
            raise RuntimeError(error_msg)
        
        logger.info("音频提取成功")
    
    def generate_subtitles(self, audio_path, language='auto', **kwargs):
        """
        生成字幕
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（'auto' 为自动检测）
            **kwargs: 其他 Whisper 参数
            
        Returns:
            {
                'subtitles': [{'startTime': 0.0, 'endTime': 1.5, 'text': '...', 'translation': ''}, ...],
                'language': 'zh',
                'count': 10
            }
        """
        # 加载模型
        model = self._load_model()
        
        # 准备参数
        lang_arg = None if (language in (None, '', 'auto')) else language
        
        # 默认参数
        transcribe_params = {
            'language': lang_arg,
            'task': 'transcribe',
            'beam_size': 20,
            'temperature': 0.0,
            'condition_on_previous_text': True,
            'compression_ratio_threshold': 2.0,
            'log_prob_threshold': -0.8,
            'no_speech_threshold': 0.6,
            'vad_filter': False,
            'word_timestamps': False,
        }
        
        # 合并用户参数
        transcribe_params.update(kwargs)
        
        logger.info(f"开始转录: {audio_path}")
        logger.info(f"参数: {transcribe_params}")
        
        # 执行转录
        segments, info = model.transcribe(str(audio_path), **transcribe_params)
        
        # 转换为字幕格式
        subtitles = []
        for seg in segments:
            subtitle = {
                'startTime': float(seg.start or 0),
                'endTime': float(seg.end or 0),
                'text': (seg.text or '').strip(),
                'translation': ''
            }
            if subtitle['text']:
                subtitles.append(subtitle)
        
        detected_language = getattr(info, 'language', '') or ''
        
        logger.info(f"转录完成: 生成 {len(subtitles)} 条字幕")
        logger.info(f"检测语言: {detected_language}")
        
        return {
            'subtitles': subtitles,
            'language': detected_language,
            'count': len(subtitles)
        }
    
    def release_model(self):
        """释放模型内存"""
        if self.model is not None:
            del self.model
            self.model = None
            
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("已清理 CUDA 缓存")
            except ImportError:
                pass
            
            logger.info("Whisper 模型已释放")
    
    def __del__(self):
        """析构函数，确保释放资源"""
        self.release_model()
