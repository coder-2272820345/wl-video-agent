"""
语音合成模块（TTS）
使用edge-tts或阿里云TTS将文本转换为语音
"""
import logging
import asyncio
from pathlib import Path
from typing import Optional

from config import AUDIO_DIR, DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)


class TTSGenerator:
    """语音合成器类"""

    def __init__(self):
        """初始化TTSGenerator"""
        self.audio_dir = AUDIO_DIR
        logger.info(f"TTSGenerator initialized with audio dir: {self.audio_dir}")

    def synthesize(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        output_path: Optional[str] = None
    ) -> str:
        """
        将文本合成为语音
        
        Args:
            text: 要合成的文本内容
            voice: 语音类型，默认使用微软晓晓
            output_path: 输出音频文件路径，默认自动生成
            
        Returns:
            str: 生成的音频文件路径
            
        Raises:
            Exception: 语音合成失败时抛出异常
        """
        if not text or len(text.strip()) < 5:
            raise ValueError("待合成文本过短")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            import uuid
            audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
            output_path = str(self.audio_dir / audio_filename)
        
        try:
            logger.info(f"Synthesizing speech for text ({len(text)} characters)")
            
            # 优先使用免费的edge-tts
            result_path = self._synthesize_with_edge_tts(text, voice, output_path)
            
            if result_path:
                logger.info(f"TTS completed successfully: {result_path}")
                return result_path
            else:
                # 备选方案：使用阿里云TTS
                logger.warning("edge-tts failed, falling back to Alibaba Cloud TTS")
                return self._synthesize_with_aliyun(text, voice, output_path)
                
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {str(e)}")
            raise Exception(f"语音合成失败: {str(e)}") from e

    def _synthesize_with_edge_tts(
        self,
        text: str,
        voice: str,
        output_path: str
    ) -> Optional[str]:
        """
        使用edge-tts进行语音合成（免费）
        
        Args:
            text: 待合成文本
            voice: 语音类型
            output_path: 输出路径
            
        Returns:
            Optional[str]: 音频文件路径，失败返回None
        """
        try:
            import edge_tts
            
            # 创建Communicate对象
            communicate = edge_tts.Communicate(text, voice)
            
            # 异步保存音频
            asyncio.run(communicate.save(output_path))
            
            # 验证文件是否生成
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                logger.info(f"edge-tts generated file: {output_path} ({file_size / 1024:.2f} KB)")
                return output_path
            else:
                logger.warning("edge-tts output file not found")
                return None
                
        except ImportError:
            logger.warning("edge-tts package not installed")
            return None
        except Exception as e:
            logger.error(f"edge-tts error: {str(e)}")
            return None

    def _synthesize_with_aliyun(
        self,
        text: str,
        voice: str,
        output_path: str
    ) -> str:
        """
        使用阿里云TTS进行语音合成（备选方案）
        
        Args:
            text: 待合成文本
            voice: 语音类型
            output_path: 输出路径
            
        Returns:
            str: 音频文件路径
            
        Raises:
            Exception: 阿里云TTS调用失败
        """
        try:
            import dashscope
            from dashscope.audio.tts import SpeechSynthesizer
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            # 调用语音合成API
            result = SpeechSynthesizer.call(
                model='sambert-zhichu-v1',  # 使用知初模型
                text=text,
                voice=voice,
                format='mp3',
                sample_rate=48000
            )
            
            if result.status_code == 200:
                # 保存音频文件
                with open(output_path, 'wb') as f:
                    f.write(result.get_audio_data())
                
                logger.info(f"Aliyun TTS generated file: {output_path}")
                return output_path
            else:
                raise Exception(f"Aliyun TTS API error: {result.message}")
                
        except ImportError:
            raise Exception("dashscope package not installed")
        except Exception as e:
            logger.error(f"Aliyun TTS error: {str(e)}")
            raise Exception(f"阿里云TTS失败: {str(e)}") from e

    @staticmethod
    def get_available_voices() -> list:
        """
        获取可用的语音列表
        
        Returns:
            list: 可用语音列表
        """
        return [
            "zh-CN-XiaoxiaoNeural",  # 微软晓晓（女声）
            "zh-CN-YunxiNeural",     # 云希（男声）
            "zh-CN-XiaoyiNeural",    # 晓伊（女声）
            "zh-CN-YunjianNeural",   # 云健（男声）
        ]
