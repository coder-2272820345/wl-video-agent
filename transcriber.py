"""
语音转文字模块
使用FFmpeg提取音频，并使用阿里云语音识别或Whisper进行转录
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional
import os

from config import AUDIO_DIR, FFMPEG_PATH, FFPROBE_PATH, DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)


class VideoTranscriber:
    """视频转录器类"""

    def __init__(self):
        """初始化VideoTranscriber"""
        self.audio_dir = AUDIO_DIR
        logger.info(f"VideoTranscriber initialized with audio dir: {self.audio_dir}")

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径，默认自动生成
            
        Returns:
            str: 提取的音频文件路径（mp3格式）
            
        Raises:
            Exception: 音频提取失败时抛出异常
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            audio_filename = f"{video_path.stem}.mp3"
            output_path = str(self.audio_dir / audio_filename)
        
        try:
            logger.info(f"Extracting audio from {video_path} to {output_path}")
            
            # 使用FFmpeg提取音频
            cmd = [
                FFMPEG_PATH,
                '-i', str(video_path),
                '-vn',  # 不处理视频
                '-acodec', 'libmp3lame',  # MP3编码
                '-ab', '192k',  # 比特率
                '-ar', '44100',  # 采样率
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg错误: {error_msg}")
            
            # 验证输出文件
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"音频文件未生成: {output_path}")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Audio extracted successfully: {output_path} ({file_size / 1024 / 1024:.2f} MB)")
            
            return output_path
            
        except subprocess.TimeoutExpired:
            raise Exception("音频提取超时")
        except Exception as e:
            logger.error(f"Failed to extract audio: {str(e)}")
            raise Exception(f"音频提取失败: {str(e)}") from e

    def transcribe(self, audio_path: str, language: str = 'zh') -> str:
        """
        将音频转换为文字
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码，默认中文'zh'
            
        Returns:
            str: 转录的文字内容
            
        Raises:
            Exception: 转录失败时抛出异常
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # 优先使用阿里云DashScope语音识别
            transcript = self._transcribe_with_dashscope(str(audio_path), language)
            
            if transcript:
                logger.info(f"Transcription completed: {len(transcript)} characters")
                return transcript
            else:
                # 备选方案：使用Whisper（需要安装openai-whisper）
                logger.warning("DashScope transcription failed, falling back to Whisper")
                return self._transcribe_with_whisper(str(audio_path), language)
                
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {str(e)}")
            raise Exception(f"语音转文字失败: {str(e)}") from e

    def _transcribe_with_dashscope(self, audio_path: str, language: str) -> Optional[str]:
        """
        使用阿里云DashScope进行语音识别
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            Optional[str]: 转录文本，失败返回None
        """
        try:
            import dashscope
            from dashscope.audio.asr import Recognition
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            # 创建识别实例
            recognition = Recognition(
                model='paraformer-v2',  # 使用Paraformer模型
                format='mp3',
                sample_rate=44100,
                callback=None
            )
            
            # 调用识别API
            result = recognition.call(audio_path)
            
            if result.status_code == 200:
                # 解析结果
                transcript = ''
                for sentence in result.output.get('sentences', []):
                    transcript += sentence.get('text', '')
                
                return transcript.strip()
            else:
                logger.warning(f"DashScope API error: {result.message}")
                return None
                
        except ImportError:
            logger.warning("dashscope package not installed")
            return None
        except Exception as e:
            logger.error(f"DashScope transcription error: {str(e)}")
            return None

    def _transcribe_with_whisper(self, audio_path: str, language: str) -> str:
        """
        使用OpenAI Whisper进行语音识别（备选方案）
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            str: 转录文本
            
        Raises:
            Exception: Whisper转录失败
        """
        try:
            import whisper
            
            # 加载模型（使用base模型，平衡速度和精度）
            model = whisper.load_model("base")
            
            # 执行转录
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )
            
            transcript = result.get('text', '').strip()
            
            if not transcript:
                raise Exception("Whisper returned empty transcript")
            
            return transcript
            
        except ImportError:
            raise Exception("Whisper未安装，请运行: pip install openai-whisper")
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            raise Exception(f"Whisper转录失败: {str(e)}") from e
