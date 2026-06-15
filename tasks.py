"""
Celery异步任务模块
定义视频创作全流程的异步任务
"""
import logging
from typing import Dict, Any
from pathlib import Path

from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_MAX_RETRIES, CELERY_RETRY_DELAY

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Celery应用
celery_app = Celery(
    'video_agent_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3000,  # 50分钟软超时
)


@celery_app.task(bind=True, max_retries=CELERY_MAX_RETRIES, name='analyze_and_generate_script')
def analyze_and_generate_script(
    self,
    video_url: str,
    topic: str,
    duration_seconds: int = 60
) -> Dict[str, Any]:
    """
    分析视频风格并生成新脚本的完整流程
    
    流程：下载视频 -> 提取音频 -> 语音转文字 -> 分析风格 -> 生成新脚本
    
    Args:
        video_url: 参考视频URL
        topic: 要生成的新视频主题
        duration_seconds: 目标视频时长（秒）
        
    Returns:
        Dict[str, Any]: 包含分析结果和生成脚本的字典
        
    Raises:
        Exception: 任一环节失败时抛出异常
    """
    try:
        logger.info(f"Starting analyze_and_generate_script task: URL={video_url}, Topic={topic}")
        
        # 步骤1: 下载视频
        logger.info("Step 1: Downloading video...")
        from downloader import VideoDownloader
        downloader = VideoDownloader()
        video_path = downloader.download(video_url)
        logger.info(f"Video downloaded to: {video_path}")
        
        # 步骤2: 提取音频
        logger.info("Step 2: Extracting audio...")
        from transcriber import VideoTranscriber
        transcriber = VideoTranscriber()
        audio_path = transcriber.extract_audio(video_path)
        logger.info(f"Audio extracted to: {audio_path}")
        
        # 步骤3: 语音转文字
        logger.info("Step 3: Transcribing audio to text...")
        transcript_text = transcriber.transcribe(audio_path)
        logger.info(f"Transcription completed: {len(transcript_text)} characters")
        
        # 步骤4: 分析风格
        logger.info("Step 4: Analyzing video style...")
        from style_analyzer import StyleAnalyzer
        analyzer = StyleAnalyzer()
        reference_style = analyzer.analyze(transcript_text)
        logger.info(f"Style analysis completed: {reference_style}")
        
        # 步骤5: 生成新脚本
        logger.info("Step 5: Generating new script...")
        from script_generator import ScriptGenerator
        generator = ScriptGenerator()
        new_script = generator.generate_script(topic, reference_style, duration_seconds)
        logger.info(f"Script generated: {len(new_script)} characters")
        
        # 返回完整结果
        result = {
            "status": "success",
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "transcript": transcript_text,
            "reference_style": reference_style,
            "generated_script": new_script,
            "duration_seconds": duration_seconds
        }
        
        logger.info("Task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        
        # 重试逻辑
        retry_in = CELERY_RETRY_DELAY * (2 ** self.request.retries)
        logger.info(f"Retrying in {retry_in} seconds... (attempt {self.request.retries + 1})")
        
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True, max_retries=CELERY_MAX_RETRIES, name='generate_video_from_script')
def generate_video_from_script(
    self,
    script: str,
    character_description: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    video_provider: str = "kling"
) -> Dict[str, Any]:
    """
    根据脚本生成视频的完整流程
    
    流程：TTS合成音频 -> 生成角色图 -> 调用图生视频API
    
    Args:
        script: 口播脚本文本
        character_description: 角色描述
        voice: TTS语音类型
        video_provider: 视频生成提供商（'kling'或'tongyi'）
        
    Returns:
        Dict[str, Any]: 包含生成结果的字典
        
    Raises:
        Exception: 任一环节失败时抛出异常
    """
    try:
        logger.info(f"Starting generate_video_from_script task")
        
        # 步骤1: TTS合成音频
        logger.info("Step 1: Synthesizing audio from script...")
        from tts_generator import TTSGenerator
        tts_generator = TTSGenerator()
        audio_path = tts_generator.synthesize(script, voice)
        logger.info(f"Audio synthesized to: {audio_path}")
        
        # 步骤2: 生成角色图像
        logger.info("Step 2: Generating character image...")
        from image_generator import ImageGenerator
        image_generator = ImageGenerator()
        image_path = image_generator.generate_character(character_description)
        logger.info(f"Character image generated: {image_path}")
        
        # 步骤3: 生成视频
        logger.info("Step 3: Generating video from image and audio...")
        from video_generator import VideoGenerator
        video_generator = VideoGenerator()
        
        # 估算视频时长（根据音频长度）
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = int(float(result.stdout.strip()))
        
        video_url = video_generator.image_to_video(
            image_url=image_path,
            audio_url=audio_path,
            prompt=f"角色口播，{character_description}，自然说话动作",
            provider=video_provider,
            duration=min(duration, 30)  # 限制最长30秒
        )
        logger.info(f"Video generated: {video_url}")
        
        # 返回完整结果
        result = {
            "status": "success",
            "audio_path": str(audio_path),
            "image_path": str(image_path),
            "video_url": video_url,
            "script": script,
            "duration": duration
        }
        
        logger.info("Task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        
        # 重试逻辑
        retry_in = CELERY_RETRY_DELAY * (2 ** self.request.retries)
        logger.info(f"Retrying in {retry_in} seconds... (attempt {self.request.retries + 1})")
        
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True, max_retries=CELERY_MAX_RETRIES, name='compose_final_video')
def compose_final_video(
    self,
    video_segments: list,
    audio: str,
    script_text: str,
    vertical: bool = True
) -> Dict[str, Any]:
    """
    合成最终视频的完整流程
    
    流程：生成字幕 -> 拼接视频 -> 添加音频 -> 添加字幕 -> 转竖屏
    
    Args:
        video_segments: 视频片段路径列表
        audio: 音频文件路径
        script_text: 脚本文本（用于生成字幕）
        vertical: 是否转为竖屏格式
        
    Returns:
        Dict[str, Any]: 包含最终视频信息的字典
        
    Raises:
        Exception: 任一环节失败时抛出异常
    """
    try:
        logger.info(f"Starting compose_final_video task with {len(video_segments)} segments")
        
        # 步骤1: 生成字幕
        logger.info("Step 1: Generating subtitles from script...")
        from subtitle_generator import SubtitleGenerator
        subtitle_gen = SubtitleGenerator()
        
        # 获取音频时长
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        audio_duration = float(result.stdout.strip())
        
        srt_path = subtitle_gen.generate_from_script(script_text, audio_duration)
        logger.info(f"Subtitles generated: {srt_path}")
        
        # 步骤2: 合成完整视频
        logger.info("Step 2: Composing full video...")
        from video_editor import VideoEditor
        editor = VideoEditor()
        
        final_video = editor.compose_full_video(
            clips=video_segments,
            audio=audio,
            subtitles=srt_path,
            vertical=vertical
        )
        logger.info(f"Final video composed: {final_video}")
        
        # 返回完整结果
        result = {
            "status": "success",
            "final_video": str(final_video),
            "subtitle_file": str(srt_path),
            "audio": audio,
            "segments_count": len(video_segments),
            "vertical": vertical
        }
        
        logger.info("Task completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        
        # 重试逻辑
        retry_in = CELERY_RETRY_DELAY * (2 ** self.request.retries)
        logger.info(f"Retrying in {retry_in} seconds... (attempt {self.request.retries + 1})")
        
        raise self.retry(exc=e, countdown=retry_in)
