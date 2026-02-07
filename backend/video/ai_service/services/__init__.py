"""
AI 服务层
提供各种 AI 功能的封装服务
"""
from .whisper_service import WhisperService
from .ocr_service import OCRService

__all__ = [
    'WhisperService',
    'OCRService',
]
