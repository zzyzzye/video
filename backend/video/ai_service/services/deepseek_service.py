"""
DeepSeek API 服务
用于调用 DeepSeek AI 模型进行文本处理
"""
from openai import OpenAI
from typing import Optional, Dict, List
from django.conf import settings


class DeepSeekService:
    """DeepSeek API 调用服务"""
    
    def __init__(self):
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """
        调用 DeepSeek Chat Completion API
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性 (0-2)
            max_tokens: 最大生成 token 数
            stream: 是否使用流式输出
            
        Returns:
            API 响应结果（转换为字典格式）
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            # 转换为字典格式，保持与原来的接口一致
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
            raise Exception(f"DeepSeek API 调用失败: {str(e)}")
    
    def optimize_subtitle(self, subtitle_text: str) -> str:
        """
        优化字幕文本
        
        Args:
            subtitle_text: 原始字幕文本
            
        Returns:
            优化后的字幕文本
        """
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
        
        result = self.chat_completion(messages, temperature=0.3)
        return result['choices'][0]['message']['content']
    
    def translate_subtitle(self, subtitle_text: str, target_language: str = "英文") -> str:
        """
        翻译字幕
        
        Args:
            subtitle_text: 原始字幕文本
            target_language: 目标语言
            
        Returns:
            翻译后的字幕文本
        """
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
        
        result = self.chat_completion(messages, temperature=0.3)
        return result['choices'][0]['message']['content']
    
    def generate_video_summary(self, subtitle_text: str) -> str:
        """
        根据字幕生成视频摘要
        
        Args:
            subtitle_text: 字幕文本
            
        Returns:
            视频摘要
        """
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
        
        result = self.chat_completion(messages, temperature=0.5, max_tokens=500)
        return result['choices'][0]['message']['content']
    
    def generate_video_tags(self, title: str, description: str, subtitle_text: str = "") -> List[str]:
        """
        生成视频标签
        
        Args:
            title: 视频标题
            description: 视频描述
            subtitle_text: 字幕文本（可选）
            
        Returns:
            标签列表
        """
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
        
        result = self.chat_completion(messages, temperature=0.7, max_tokens=200)
        tags_text = result['choices'][0]['message']['content']
        
        # 解析标签
        tags = [tag.strip() for tag in tags_text.replace('，', ',').split(',')]
        return [tag for tag in tags if tag]
