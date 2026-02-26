"""
DeepSeek API 服务
用于调用 DeepSeek AI 模型进行文本处理
"""
from openai import AsyncOpenAI
from typing import Optional, Dict, List
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)


class DeepSeekService:
    """DeepSeek API 调用服务 (支持异步与重试机制)"""
    
    def __init__(self):
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 使用异步客户端
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    @retry(
        stop=stop_after_attempt(3),  # 最多重试 3 次
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数级等待：2s, 4s, 8s...
        retry=retry_if_exception_type(Exception),  # 遇到任何 Exception 都重试 (生产环境建议缩小范围)
        before_sleep=lambda retry_state: logger.warning(f"DeepSeek API 调用失败，正在进行第 {retry_state.attempt_number} 次重试...")
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """
        异步调用 DeepSeek Chat Completion API，并具备自动重试机制
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            return {
                'choices': [
                    {
                        'message': {
                            'content': response.choices[0].message.content,
                            'role': response.choices[0].message.role
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"DeepSeek API 调用最终失败: {str(e)}")
            raise

    async def optimize_subtitle(self, subtitle_text: str) -> str:
        """异步优化字幕文本"""
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的字幕优化助手。请优化字幕文本，修正错别字、标点符号，使其更加通顺易读。保持原意不变。"
            },
            {
                "role": "user",
                "content": f"请优化以下字幕文本：\n\n{subtitle_text}"
            }
        ]
        
        result = await self.chat_completion(messages, temperature=0.3)
        return result['choices'][0]['message']['content']

    async def translate_subtitle(self, subtitle_text: str, target_language: str = "英文") -> str:
        """异步翻译字幕"""
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的字幕翻译助手。请将字幕翻译成{target_language}，保持时间轴格式不变。"
            },
            {
                "role": "user",
                "content": f"请翻译以下字幕：\n\n{subtitle_text}"
            }
        ]
        
        result = await self.chat_completion(messages, temperature=0.3)
        return result['choices'][0]['message']['content']

    async def generate_video_summary(self, subtitle_text: str) -> str:
        """异步生成视频摘要"""
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频内容分析助手。请根据字幕内容生成简洁的视频摘要。"
            },
            {
                "role": "user",
                "content": f"请根据以下字幕生成视频摘要（200字以内）：\n\n{subtitle_text}"
            }
        ]
        
        result = await self.chat_completion(messages, temperature=0.5, max_tokens=500)
        return result['choices'][0]['message']['content']

    async def generate_video_tags(self, title: str, description: str, subtitle_text: str = "") -> List[str]:
        """异步生成视频标签"""
        content = f"标题：{title}\n描述：{description}"
        if subtitle_text:
            content += f"\n字幕片段：{subtitle_text[:500]}"
            
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频标签生成助手。请根据视频信息生成5-10个相关标签，用逗号分隔。"
            },
            {
                "role": "user",
                "content": f"请为以下视频生成标签：\n\n{content}"
            }
        ]
        
        result = await self.chat_completion(messages, temperature=0.7, max_tokens=200)
        tags_text = result['choices'][0]['message']['content']
        
        tags = [tag.strip() for tag in tags_text.replace('，', ',').split(',')]
        return [tag for tag in tags if tag]
