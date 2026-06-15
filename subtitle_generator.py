"""
字幕生成模块
使用FFmpeg或阿里云语音识别生成SRT字幕文件
"""
import logging
import re
from pathlib import Path
from typing import Optional

from config import AUDIO_DIR, DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """字幕生成器类"""

    def __init__(self):
        """初始化SubtitleGenerator"""
        self.audio_dir = AUDIO_DIR
        logger.info(f"SubtitleGenerator initialized with audio dir: {self.audio_dir}")

    def generate_from_audio(
        self,
        audio_path: str,
        text: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        根据音频和文本生成SRT字幕文件
        
        Args:
            audio_path: 音频文件路径
            text: 对应的文本内容
            output_path: 输出SRT文件路径，默认自动生成
            
        Returns:
            str: 生成的SRT字幕文件路径
            
        Raises:
            Exception: 字幕生成失败时抛出异常
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        if not text or len(text.strip()) < 10:
            raise ValueError("文本内容过短，无法生成字幕")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            srt_filename = f"{Path(audio_path).stem}.srt"
            output_path = str(Path(audio_path).parent / srt_filename)
        
        try:
            logger.info(f"Generating SRT subtitles from audio and text")
            
            # 尝试使用阿里云语音识别获取时间戳
            srt_content = self._generate_with_timestamps(audio_path, text)
            
            if srt_content:
                # 保存SRT文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                
                logger.info(f"SRT subtitles generated: {output_path}")
                return output_path
            else:
                # 备选方案：简单分段生成
                logger.warning("Using simple segmentation for subtitles")
                return self._generate_simple_srt(text, output_path)
                
        except Exception as e:
            logger.error(f"Failed to generate subtitles: {str(e)}")
            raise Exception(f"字幕生成失败: {str(e)}") from e

    def _generate_with_timestamps(self, audio_path: str, text: str) -> Optional[str]:
        """
        使用阿里云语音识别生成带时间戳的字幕
        
        Args:
            audio_path: 音频文件路径
            text: 文本内容
            
        Returns:
            Optional[str]: SRT格式字幕，失败返回None
        """
        try:
            import dashscope
            from dashscope.audio.asr import Recognition
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            # 创建识别实例（启用时间戳）
            recognition = Recognition(
                model='paraformer-v2',
                format='mp3',
                sample_rate=44100,
                callback=None
            )
            
            # 调用识别API
            result = recognition.call(audio_path)
            
            if result.status_code == 200:
                # 解析带时间戳的结果
                sentences = result.output.get('sentences', [])
                
                if sentences:
                    srt_content = self._convert_to_srt(sentences)
                    return srt_content
                else:
                    logger.warning("No sentences in ASR result")
                    return None
            else:
                logger.warning(f"DashScope API error: {result.message}")
                return None
                
        except ImportError:
            logger.warning("dashscope package not installed")
            return None
        except Exception as e:
            logger.error(f"DashScope ASR error: {str(e)}")
            return None

    def _convert_to_srt(self, sentences: list) -> str:
        """
        将阿里云ASR结果转换为SRT格式
        
        Args:
            sentences: ASR返回的句子列表，每个句子包含text、begin_time、end_time
            
        Returns:
            str: SRT格式字幕
        """
        srt_lines = []
        
        for idx, sentence in enumerate(sentences, start=1):
            text = sentence.get('text', '').strip()
            begin_time = sentence.get('begin_time', 0)  # 毫秒
            end_time = sentence.get('end_time', 0)  # 毫秒
            
            if not text:
                continue
            
            # 转换时间格式：毫秒 -> HH:MM:SS,mmm
            start_str = self._ms_to_srt_time(begin_time)
            end_str = self._ms_to_srt_time(end_time)
            
            # 添加SRT条目
            srt_lines.append(str(idx))
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(text)
            srt_lines.append("")  # 空行分隔
        
        return '\n'.join(srt_lines)

    def _generate_simple_srt(self, text: str, output_path: str) -> str:
        """
        简单分段生成SRT字幕（不带精确时间戳）
        
        Args:
            text: 完整文本
            output_path: 输出路径
            
        Returns:
            str: SRT文件路径
        """
        try:
            # 将文本按句子分割
            sentences = re.split(r'[。！？!?；;]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 估算每句的时长（假设每秒3.5个字）
            chars_per_second = 3.5
            current_time = 0
            
            srt_lines = []
            
            for idx, sentence in enumerate(sentences, start=1):
                if not sentence:
                    continue
                
                # 计算这句的时长
                duration = len(sentence) / chars_per_second
                start_time = current_time * 1000  # 转换为毫秒
                end_time = (current_time + duration) * 1000
                
                # 转换时间格式
                start_str = self._ms_to_srt_time(int(start_time))
                end_str = self._ms_to_srt_time(int(end_time))
                
                # 添加SRT条目
                srt_lines.append(str(idx))
                srt_lines.append(f"{start_str} --> {end_str}")
                srt_lines.append(sentence)
                srt_lines.append("")
                
                current_time += duration
            
            srt_content = '\n'.join(srt_lines)
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Simple SRT generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate simple SRT: {str(e)}")
            raise Exception(f"简单字幕生成失败: {str(e)}") from e

    @staticmethod
    def _ms_to_srt_time(milliseconds: int) -> str:
        """
        将毫秒转换为SRT时间格式 (HH:MM:SS,mmm)
        
        Args:
            milliseconds: 毫秒数
            
        Returns:
            str: SRT时间格式字符串
        """
        hours = milliseconds // 3600000
        minutes = (milliseconds % 3600000) // 60000
        seconds = (milliseconds % 60000) // 1000
        ms = milliseconds % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def generate_from_script(
        self,
        script: str,
        audio_duration: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        根据脚本和音频时长生成均匀分布的字幕
        
        Args:
            script: 脚本文本
            audio_duration: 音频时长（秒）
            output_path: 输出SRT文件路径
            
        Returns:
            str: SRT文件路径
        """
        try:
            # 将脚本按句子分割
            sentences = re.split(r'[。！？!?；;。\n]', script)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                raise ValueError("脚本内容为空")
            
            # 计算每句的平均时长
            total_chars = sum(len(s) for s in sentences)
            chars_per_second = total_chars / audio_duration if audio_duration > 0 else 3.5
            
            current_time = 0.0
            srt_lines = []
            
            for idx, sentence in enumerate(sentences, start=1):
                if not sentence:
                    continue
                
                # 计算这句的时长
                duration = len(sentence) / chars_per_second
                start_time = current_time * 1000
                end_time = (current_time + duration) * 1000
                
                # 转换时间格式
                start_str = self._ms_to_srt_time(int(start_time))
                end_str = self._ms_to_srt_time(int(end_time))
                
                # 添加SRT条目
                srt_lines.append(str(idx))
                srt_lines.append(f"{start_str} --> {end_str}")
                srt_lines.append(sentence)
                srt_lines.append("")
                
                current_time += duration
            
            srt_content = '\n'.join(srt_lines)
            
            # 如果没有指定输出路径，自动生成
            if output_path is None:
                import uuid
                output_path = str(self.audio_dir / f"subtitle_{uuid.uuid4().hex[:8]}.srt")
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Script-based SRT generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate script-based SRT: {str(e)}")
            raise Exception(f"基于脚本的字幕生成失败: {str(e)}") from e
