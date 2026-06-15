"""
项目配置文件
包含所有API Key、路径配置和常量定义
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== API Keys ====================
# 阿里云DashScope API Key（通义千问、通义万相）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "YOUR_DASHSCOPE_API_KEY")

# 腾讯云 SecretId/SecretKey（用于语音识别等）
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "YOUR_TENCENT_SECRET_ID")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "YOUR_TENCENT_SECRET_KEY")

# 可灵API Access Key（图生视频）
KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "YOUR_KLING_ACCESS_KEY")

# ==================== Redis配置 ====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ==================== 路径配置 ====================
# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 存储目录
STORAGE_DIR = BASE_DIR / "storage"
VIDEO_DOWNLOAD_DIR = STORAGE_DIR / "videos" / "downloads"
AUDIO_DIR = STORAGE_DIR / "audio"
OUTPUT_DIR = STORAGE_DIR / "output"
TEMP_DIR = STORAGE_DIR / "temp"

# 确保目录存在
for directory in [VIDEO_DOWNLOAD_DIR, AUDIO_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== FFmpeg配置 ====================
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")  # 假设ffmpeg在PATH中
FFPROBE_PATH = os.getenv("FFPROBE_PATH", "ffprobe")

# ==================== Celery配置 ====================
CELERY_TASK_TIME_LIMIT = 3600  # 任务超时时间（秒）
CELERY_TASK_SOFT_TIME_LIMIT = 3000  # 软超时时间（秒）
CELERY_MAX_RETRIES = 3  # 最大重试次数
CELERY_RETRY_DELAY = 60  # 重试延迟（秒）

# ==================== 视频生成配置 ====================
DEFAULT_VIDEO_DURATION = 60  # 默认视频时长（秒）
SUPPORTED_PLATFORMS = ["youtube", "douyin", "bilibili", "tiktok"]  # 支持的视频平台
