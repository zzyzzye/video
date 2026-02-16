"""
NSFW 视频内容检测服务
使用 Freepik/nsfw_image_detector 模型
"""
import os
import cv2
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple
from transformers import AutoModelForImageClassification
from timm.data.transforms_factory import create_transform
from timm.data import resolve_data_config
from timm.models import get_pretrained_cfg
from torchvision.transforms import Compose
import torch.nn.functional as F
import logging

logger = logging.getLogger(__name__)


class NSFWDetector:
    """NSFW 内容检测器"""
    
    # 单例模式
    _instance = None
    _model = None
    _processor = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化检测器（延迟加载）"""
        self.idx_to_label = {0: 'neutral', 1: 'low', 2: 'medium', 3: 'high'}
    
    def _load_model(self, model_path: str):
        """加载模型（延迟加载）"""
        if self._model is not None:
            return
        
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"NSFW 检测器使用设备: {self._device}")
        
        if torch.cuda.is_available():
            logger.info(f"CUDA 设备: {torch.cuda.get_device_name(0)}")
        
        # 加载模型
        abs_model_path = os.path.abspath(model_path)
        logger.info(f"加载 NSFW 模型: {abs_model_path}")
        
        self._model = AutoModelForImageClassification.from_pretrained(
            abs_model_path,
            torch_dtype=torch.bfloat16,
            local_files_only=True
        ).to(self._device)
        self._model.eval()
        
        # 加载图像预处理器
        cfg = get_pretrained_cfg("eva02_base_patch14_448.mim_in22k_ft_in22k_in1k")
        self._processor = create_transform(**resolve_data_config(cfg.__dict__))
        
        logger.info("NSFW 模型加载完成")
    
    def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, float]]:
        """
        批量预测图像的 NSFW 分数
        
        Args:
            images: PIL 图像列表
            
        Returns:
            每张图像的 NSFW 分数字典列表
        """
        if self._model is None or self._processor is None:
            raise RuntimeError("模型未加载，请先调用 _load_model")
        
        # 预处理图像
        inputs = torch.stack([self._processor(img) for img in images]).to(self._device)
        
        output = []
        with torch.inference_mode():
            logits = self._model(inputs).logits
            batch_probs = F.log_softmax(logits, dim=-1)
            batch_probs = torch.exp(batch_probs).cpu()
            
            for i in range(len(batch_probs)):
                element_probs = batch_probs[i]
                output_img = {}
                danger_cum_sum = 0
                
                # 计算累积概率
                for j in range(len(element_probs) - 1, -1, -1):
                    danger_cum_sum += element_probs[j]
                    if j == 0:
                        danger_cum_sum = element_probs[j]
                    output_img[self.idx_to_label[j]] = danger_cum_sum.item()
                output.append(output_img)
        
        return output
    
    def extract_frames(self, video_path: str, fps: int = 1) -> List[Tuple]:
        """
        从视频中抽取帧
        
        Args:
            video_path: 视频文件路径
            fps: 每秒抽取的帧数
            
        Returns:
            (帧图像, 帧编号, 时间戳)的列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0:
            video_fps = 25  # 默认 FPS
        
        frame_interval = max(1, int(video_fps / fps))
        
        frames = []
        frame_count = 0
        extracted_count = 0
        
        logger.info(f"视频 FPS: {video_fps}, 抽帧间隔: {frame_interval}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # OpenCV 读取的是 BGR 格式，转换为 RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                timestamp = frame_count / video_fps
                frames.append((pil_image, frame_count, timestamp))
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        logger.info(f"总帧数: {frame_count}, 抽取帧数: {extracted_count}")
        return frames
    
    def detect_video(
        self,
        video_path: str,
        model_path: str,
        threshold_level: str = "medium",
        threshold: float = 0.6,
        fps: int = 1,
        batch_size: int = 4,
        save_frames: bool = True,
        frames_dir: str = None,
        progress_callback: callable = None
    ) -> Dict:
        """
        检测视频 NSFW 内容
        
        Args:
            video_path: 视频文件路径
            model_path: 模型路径
            threshold_level: 阈值级别 (low/medium/high)
            threshold: 置信度阈值
            fps: 每秒抽取的帧数
            batch_size: 批处理大小
            save_frames: 是否保存问题帧图片
            frames_dir: 保存帧图片的目录
            progress_callback: 进度回调函数 callback(current, total, flagged_frames)
            
        Returns:
            检测结果字典
        """
        # 加载模型
        self._load_model(model_path)
        
        # 抽取帧
        logger.info(f"开始处理视频: {video_path}")
        frames_data = self.extract_frames(video_path, fps)
        
        if not frames_data:
            return {
                'is_safe': True,
                'flagged_count': 0,
                'total_frames': 0,
                'flagged_frames': [],
                'max_scores': {'neutral': 1.0, 'low': 0.0, 'medium': 0.0, 'high': 0.0}
            }
        
        # 创建保存目录
        if save_frames and frames_dir:
            Path(frames_dir).mkdir(parents=True, exist_ok=True)
        
        # 批量处理
        flagged_frames = []
        max_scores = {'neutral': 0.0, 'low': 0.0, 'medium': 0.0, 'high': 0.0}
        total_frames = len(frames_data)
        
        for i in range(0, total_frames, batch_size):
            batch = frames_data[i:i + batch_size]
            images = [item[0] for item in batch]
            
            # 预测
            predictions = self.predict_batch(images)
            
            # 检查并记录有问题的帧
            for j, (image, frame_num, timestamp) in enumerate(batch):
                pred = predictions[j]
                score = pred[threshold_level]
                
                # 更新最大分数
                for level in ['neutral', 'low', 'medium', 'high']:
                    max_scores[level] = max(max_scores[level], pred[level])
                
                if score >= threshold:
                    frame_info = {
                        'frame_number': frame_num,
                        'timestamp': round(timestamp, 2),
                        'level': threshold_level,
                        'confidence': round(score, 4),
                        'scores': {k: round(v, 4) for k, v in pred.items()}
                    }
                    
                    # 保存问题帧图片
                    if save_frames and frames_dir:
                        frame_filename = f"frame_{frame_num}_{timestamp:.2f}s.jpg"
                        frame_path = os.path.join(frames_dir, frame_filename)
                        try:
                            image.save(frame_path, 'JPEG', quality=85)
                            frame_info['image_path'] = frame_filename
                            logger.info(f"保存问题帧: {frame_filename}")
                        except Exception as e:
                            logger.error(f"保存帧图片失败: {str(e)}")
                    
                    flagged_frames.append(frame_info)
            
            # 调用进度回调
            if progress_callback:
                current = min(i + batch_size, total_frames)
                try:
                    progress_callback(current, total_frames, flagged_frames)
                except Exception as e:
                    logger.error(f"进度回调失败: {str(e)}")
        
        # 判断是否安全
        is_safe = len(flagged_frames) == 0
        
        result = {
            'is_safe': is_safe,
            'flagged_count': len(flagged_frames),
            'total_frames': len(frames_data),
            'flagged_frames': flagged_frames,
            'max_scores': {k: round(v, 4) for k, v in max_scores.items()},
            'threshold_level': threshold_level,
            'threshold': threshold
        }
        
        logger.info(f"检测完成: 总帧数={len(frames_data)}, 标记帧数={len(flagged_frames)}")
        return result
    
    def release_model(self):
        """释放模型资源"""
        if self._model is not None:
            del self._model
            self._model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("NSFW 模型已释放")
