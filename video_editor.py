"""
视频编辑模块
使用FFmpeg进行视频剪辑、拼接、添加音频和字幕等操作
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from config import FFMPEG_PATH, FFPROBE_PATH, OUTPUT_DIR

logger = logging.getLogger(__name__)


class VideoEditor:
    """视频编辑器类"""

    def __init__(self):
        """初始化VideoEditor"""
        self.output_dir = OUTPUT_DIR
        logger.info(f"VideoEditor initialized with output dir: {self.output_dir}")

    def concatenate_videos(self, video_paths: List[str], output_path: Optional[str] = None) -> str:
        """
        拼接多个视频片段
        
        Args:
            video_paths: 视频文件路径列表
            output_path: 输出文件路径，默认自动生成
            
        Returns:
            str: 拼接后的视频文件路径
            
        Raises:
            Exception: 视频拼接失败时抛出异常
        """
        if not video_paths or len(video_paths) < 2:
            raise ValueError("至少需要两个视频文件才能拼接")
        
        # 验证所有视频文件存在
        for path in video_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"视频文件不存在: {path}")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            output_filename = f"concatenated_{len(video_paths)}_videos.mp4"
            output_path = str(self.output_dir / output_filename)
        
        try:
            logger.info(f"Concatenating {len(video_paths)} videos to {output_path}")
            
            # 创建临时文件列表
            concat_file = self.output_dir / "concat_list.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video_path in video_paths:
                    # 转换为绝对路径
                    abs_path = Path(video_path).resolve()
                    f.write(f"file '{abs_path}'\n")
            
            # 使用FFmpeg拼接视频
            cmd = [
                FFMPEG_PATH,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            # 删除临时文件
            concat_file.unlink(missing_ok=True)
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg错误: {error_msg}")
            
            logger.info(f"Videos concatenated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to concatenate videos: {str(e)}")
            raise Exception(f"视频拼接失败: {str(e)}") from e

    def add_audio(self, video_path: str, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        为视频添加音频
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径，默认自动生成
            
        Returns:
            str: 添加音频后的视频文件路径
            
        Raises:
            Exception: 音频添加失败时抛出异常
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            output_filename = f"{Path(video_path).stem}_with_audio.mp4"
            output_path = str(self.output_dir / output_filename)
        
        try:
            logger.info(f"Adding audio to video: {video_path} + {audio_path}")
            
            # 使用FFmpeg添加音频
            cmd = [
                FFMPEG_PATH,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',  # 以较短的流为准
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg错误: {error_msg}")
            
            logger.info(f"Audio added successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to add audio: {str(e)}")
            raise Exception(f"添加音频失败: {str(e)}") from e

    def add_subtitles(self, video_path: str, subtitle_srt: str, output_path: Optional[str] = None) -> str:
        """
        为视频添加字幕
        
        Args:
            video_path: 视频文件路径
            subtitle_srt: SRT字幕文件路径
            output_path: 输出文件路径，默认自动生成
            
        Returns:
            str: 添加字幕后的视频文件路径
            
        Raises:
            Exception: 字幕添加失败时抛出异常
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        if not Path(subtitle_srt).exists():
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_srt}")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            output_filename = f"{Path(video_path).stem}_with_subtitles.mp4"
            output_path = str(self.output_dir / output_filename)
        
        try:
            logger.info(f"Adding subtitles to video: {video_path} + {subtitle_srt}")
            
            # 使用FFmpeg添加字幕（硬字幕）
            cmd = [
                FFMPEG_PATH,
                '-i', video_path,
                '-vf', f"subtitles={subtitle_srt}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'",
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg错误: {error_msg}")
            
            logger.info(f"Subtitles added successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to add subtitles: {str(e)}")
            raise Exception(f"添加字幕失败: {str(e)}") from e

    def resize_to_vertical(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        将视频转为9:16竖屏格式
        
        Args:
            video_path: 视频文件路径
            output_path: 输出文件路径，默认自动生成
            
        Returns:
            str: 转换后的竖屏视频文件路径
            
        Raises:
            Exception: 视频转换失败时抛出异常
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            output_filename = f"{Path(video_path).stem}_vertical.mp4"
            output_path = str(self.output_dir / output_filename)
        
        try:
            logger.info(f"Resizing video to vertical (9:16): {video_path}")
            
            # 使用FFmpeg转换为9:16竖屏
            # 保持画面居中，添加模糊背景
            cmd = [
                FFMPEG_PATH,
                '-i', video_path,
                '-vf', 
                'split[original][copy];'
                '[copy]scale=ih*9/16:ih,crop=ih*9/16:ih,(gblur=sigma=20)[background];'
                '[background][original]overlay=(W-w)/2:(H-h)/2,'
                'scale=1080:1920:flags=lanczos',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg错误: {error_msg}")
            
            logger.info(f"Video resized to vertical successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to resize video: {str(e)}")
            raise Exception(f"视频转竖屏失败: {str(e)}") from e

    def compose_full_video(
        self,
        clips: List[str],
        audio: str,
        subtitles: Optional[str] = None,
        output: Optional[str] = None,
        vertical: bool = True
    ) -> str:
        """
        完整合成流程：拼接视频、添加音频、添加字幕、转竖屏
        
        Args:
            clips: 视频片段列表
            audio: 音频文件路径
            subtitles: SRT字幕文件路径（可选）
            output: 输出文件路径，默认自动生成
            vertical: 是否转为竖屏
            
        Returns:
            str: 最终合成的视频文件路径
            
        Raises:
            Exception: 视频合成失败时抛出异常
        """
        try:
            logger.info(f"Composing full video from {len(clips)} clips")
            
            # 步骤1: 拼接视频
            if len(clips) > 1:
                logger.info("Step 1: Concatenating clips...")
                concatenated = self.concatenate_videos(clips)
            else:
                concatenated = clips[0]
            
            # 步骤2: 添加音频
            logger.info("Step 2: Adding audio...")
            with_audio = self.add_audio(concatenated, audio)
            
            # 步骤3: 添加字幕（如果提供）
            if subtitles:
                logger.info("Step 3: Adding subtitles...")
                final_video = self.add_subtitles(with_audio, subtitles)
            else:
                final_video = with_audio
            
            # 步骤4: 转为竖屏（如果需要）
            if vertical:
                logger.info("Step 4: Converting to vertical format...")
                final_output = self.resize_to_vertical(final_video, output)
            else:
                final_output = final_video
            
            logger.info(f"Full video composition completed: {final_output}")
            return final_output
            
        except Exception as e:
            logger.error(f"Failed to compose full video: {str(e)}")
            raise Exception(f"视频合成失败: {str(e)}") from e
