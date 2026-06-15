"""
解说风格分析模块
使用通义千问API分析视频的解说风格特征
"""
import logging
import json
from typing import Dict, Any, Optional

from config import DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """风格分析器类"""

    def __init__(self):
        """初始化StyleAnalyzer"""
        self.api_key = DASHSCOPE_API_KEY
        logger.info("StyleAnalyzer initialized")

    def analyze(self, transcript_text: str) -> Dict[str, Any]:
        """
        分析解说风格
        
        Args:
            transcript_text: 视频转录文本
            
        Returns:
            Dict[str, Any]: 风格分析结果，包含以下字段：
                - pace: 语速 (fast/slow/medium)
                - emotion: 情感基调 (excited/calm/humorous/professional)
                - vocabulary_level: 词汇难度 (simple/professional/technical)
                - sentence_structure: 句式结构 (short/long/mixed)
                - tone: 语调风格 (casual/formal/enthusiastic)
                - target_audience: 目标受众描述
                
        Raises:
            Exception: 分析失败时抛出异常
        """
        if not transcript_text or len(transcript_text.strip()) < 10:
            raise ValueError("转录文本过短，无法进行风格分析")
        
        try:
            logger.info(f"Analyzing style for transcript ({len(transcript_text)} characters)")
            
            # 调用通义千问API
            result = self._call_qwen_api(transcript_text)
            
            if result:
                logger.info(f"Style analysis completed: {json.dumps(result, ensure_ascii=False)}")
                return result
            else:
                raise Exception("风格分析返回空结果")
                
        except Exception as e:
            logger.error(f"Failed to analyze style: {str(e)}")
            raise Exception(f"风格分析失败: {str(e)}") from e

    def _call_qwen_api(self, transcript_text: str) -> Optional[Dict[str, Any]]:
        """
        调用通义千问API进行风格分析
        
        Args:
            transcript_text: 转录文本
            
        Returns:
            Optional[Dict[str, Any]]: 风格分析结果，失败返回None
        """
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            # 构建提示词
            prompt = self._build_analysis_prompt(transcript_text)
            
            # 调用API
            response = Generation.call(
                model='qwen-max',  # 使用高质量模型
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个专业的视频内容分析师，擅长分析解说风格和文案特点。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                result_format='message',
                temperature=0.3,  # 较低温度以获得更稳定的分析结果
                top_p=0.8
            )
            
            if response.status_code == 200:
                # 解析响应
                content = response.output.choices[0].message.content
                
                # 尝试解析JSON
                try:
                    # 查找JSON部分
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        result = json.loads(json_str)
                        
                        # 验证必要字段
                        required_fields = ['pace', 'emotion', 'vocabulary_level', 'sentence_structure']
                        if all(field in result for field in required_fields):
                            return result
                        else:
                            logger.warning(f"Missing required fields in analysis result")
                            return self._get_default_style()
                    else:
                        logger.warning("No JSON found in response")
                        return self._get_default_style()
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
                    return self._get_default_style()
            else:
                logger.error(f"Qwen API error: {response.code} - {response.message}")
                return None
                
        except ImportError:
            logger.warning("dashscope package not installed")
            return None
        except Exception as e:
            logger.error(f"Qwen API call error: {str(e)}")
            return None

    def _build_analysis_prompt(self, transcript_text: str) -> str:
        """
        构建风格分析提示词
        
        Args:
            transcript_text: 转录文本
            
        Returns:
            str: 完整的提示词
        """
        # 截取前2000字符以避免token限制
        truncated_text = transcript_text[:2000] if len(transcript_text) > 2000 else transcript_text
        
        prompt = f"""请分析以下视频解说文本的风格特征，并以JSON格式返回分析结果。

解说文本：
{truncated_text}

请分析以下维度：
1. pace（语速）: "fast"（快）、"slow"（慢）、"medium"（中等）
2. emotion（情感基调）: "excited"（激动）、"calm"（平静）、"humorous"（幽默）、"professional"（专业）
3. vocabulary_level（词汇难度）: "simple"（简单）、"professional"（专业）、"technical"（技术性强）
4. sentence_structure（句式结构）: "short"（短句为主）、"long"（长句为主）、"mixed"（混合）
5. tone（语调风格）: "casual"（随意）、"formal"（正式）、"enthusiastic"（热情）
6. target_audience（目标受众）: 简短描述

请只返回JSON格式，不要有其他说明文字。示例格式：
{{
  "pace": "medium",
  "emotion": "professional",
  "vocabulary_level": "simple",
  "sentence_structure": "mixed",
  "tone": "formal",
  "target_audience": "对科技感兴趣的普通观众"
}}
"""
        return prompt

    def _get_default_style(self) -> Dict[str, Any]:
        """
        获取默认风格配置（当API调用失败时使用）
        
        Returns:
            Dict[str, Any]: 默认风格配置
        """
        return {
            "pace": "medium",
            "emotion": "calm",
            "vocabulary_level": "simple",
            "sentence_structure": "mixed",
            "tone": "casual",
            "target_audience": "普通观众"
        }
