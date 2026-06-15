"""
脚本生成模块
使用通义千问或DeepSeek生成口播文案
"""
import logging
import json
from typing import Dict, Any, Optional

from config import DASHSCOPE_API_KEY, DEFAULT_VIDEO_DURATION

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """脚本生成器类"""

    def __init__(self):
        """初始化ScriptGenerator"""
        self.api_key = DASHSCOPE_API_KEY
        logger.info("ScriptGenerator initialized")

    def generate_script(
        self,
        topic: str,
        reference_style: Dict[str, Any],
        duration_seconds: int = DEFAULT_VIDEO_DURATION
    ) -> str:
        """
        生成口播文案脚本
        
        Args:
            topic: 视频主题
            reference_style: 参考风格字典，包含pace、emotion等字段
            duration_seconds: 目标视频时长（秒），默认60秒
            
        Returns:
            str: 生成的脚本文本
            
        Raises:
            Exception: 脚本生成失败时抛出异常
        """
        if not topic or len(topic.strip()) < 5:
            raise ValueError("视频主题不能为空或过短")
        
        if duration_seconds < 10 or duration_seconds > 600:
            raise ValueError("视频时长必须在10-600秒之间")
        
        try:
            logger.info(f"Generating script for topic: {topic}, duration: {duration_seconds}s")
            logger.info(f"Reference style: {json.dumps(reference_style, ensure_ascii=False)}")
            
            # 估算字数（中文约每秒3-4个字）
            estimated_chars = duration_seconds * 3.5
            
            # 调用大模型API生成脚本
            script = self._call_llm_api(topic, reference_style, duration_seconds, estimated_chars)
            
            if script and len(script.strip()) > 50:
                logger.info(f"Script generated successfully: {len(script)} characters")
                return script.strip()
            else:
                raise Exception("生成的脚本过短或为空")
                
        except Exception as e:
            logger.error(f"Failed to generate script: {str(e)}")
            raise Exception(f"脚本生成失败: {str(e)}") from e

    def _call_llm_api(
        self,
        topic: str,
        reference_style: Dict[str, Any],
        duration_seconds: int,
        estimated_chars: float
    ) -> Optional[str]:
        """
        调用大语言模型API生成脚本
        
        Args:
            topic: 视频主题
            reference_style: 参考风格
            duration_seconds: 视频时长
            estimated_chars: 估算字数
            
        Returns:
            Optional[str]: 生成的脚本，失败返回None
        """
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            # 构建提示词
            prompt = self._build_generation_prompt(
                topic, reference_style, duration_seconds, estimated_chars
            )
            
            # 调用通义千问API
            response = Generation.call(
                model='qwen-max',
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个专业的视频脚本创作专家，擅长根据参考风格创作吸引人的口播文案。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                result_format='message',
                temperature=0.8,  # 较高温度以增加创意性
                top_p=0.9,
                max_tokens=2000
            )
            
            if response.status_code == 200:
                script = response.output.choices[0].message.content
                return script.strip()
            else:
                logger.error(f"Qwen API error: {response.code} - {response.message}")
                
                # 尝试使用DeepSeek作为备选（如果配置了DeepSeek API）
                return self._call_deepseek_api(topic, reference_style, duration_seconds, estimated_chars)
                
        except ImportError:
            logger.warning("dashscope package not installed")
            return None
        except Exception as e:
            logger.error(f"LLM API call error: {str(e)}")
            return None

    def _call_deepseek_api(
        self,
        topic: str,
        reference_style: Dict[str, Any],
        duration_seconds: int,
        estimated_chars: float
    ) -> Optional[str]:
        """
        调用DeepSeek API生成脚本（备选方案）
        
        Args:
            topic: 视频主题
            reference_style: 参考风格
            duration_seconds: 视频时长
            estimated_chars: 估算字数
            
        Returns:
            Optional[str]: 生成的脚本，失败返回None
        """
        try:
            import requests
            
            # DeepSeek API配置（需要从环境变量读取）
            deepseek_api_key = ""  # TODO: 从config读取
            if not deepseek_api_key:
                logger.warning("DeepSeek API key not configured")
                return None
            
            prompt = self._build_generation_prompt(
                topic, reference_style, duration_seconds, estimated_chars
            )
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {deepseek_api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的视频脚本创作专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.8,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                script = result['choices'][0]['message']['content']
                return script.strip()
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"DeepSeek API call error: {str(e)}")
            return None

    def _build_generation_prompt(
        self,
        topic: str,
        reference_style: Dict[str, Any],
        duration_seconds: int,
        estimated_chars: float
    ) -> str:
        """
        构建脚本生成提示词
        
        Args:
            topic: 视频主题
            reference_style: 参考风格
            duration_seconds: 视频时长
            estimated_chars: 估算字数
            
        Returns:
            str: 完整的提示词
        """
        pace = reference_style.get('pace', 'medium')
        emotion = reference_style.get('emotion', 'calm')
        vocabulary_level = reference_style.get('vocabulary_level', 'simple')
        sentence_structure = reference_style.get('sentence_structure', 'mixed')
        tone = reference_style.get('tone', 'casual')
        
        prompt = f"""请根据以下要求，创作一个关于"{topic}"的口播视频脚本。

【风格要求】
- 语速：{pace}
- 情感基调：{emotion}
- 词汇难度：{vocabulary_level}
- 句式结构：{sentence_structure}
- 语调风格：{tone}

【技术要求】
- 视频时长：{duration_seconds}秒
- 建议字数：约{int(estimated_chars)}字
- 语言：中文

【输出要求】
请直接输出脚本内容，不要添加任何标题、说明或其他格式。
脚本应该包含：
1. 开场白（吸引注意力）
2. 主体内容（信息丰富、逻辑清晰）
3. 结尾（总结或号召行动）

注意：
- 保持口语化表达，适合朗读
- 避免过于复杂的句子
- 适当使用修辞手法增强表现力
- 确保内容准确、有价值

现在开始创作脚本：
"""
        return prompt
