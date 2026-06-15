"""
视频下载模块
使用yt-dlp实现多平台视频下载功能
"""
import logging
import os
from pathlib import Path
from typing import Optional, Callable
import yt_dlp
from config import VIDEO_DOWNLOAD_DIR

logger = logging.getLogger(__name__)


class VideoDownloader:
    """视频下载器类"""

    def __init__(self):
        """初始化VideoDownloader"""
        self.download_dir = VIDEO_DOWNLOAD_DIR
        logger.info(f"VideoDownloader initialized with download dir: {self.download_dir}")

    def download(
        self,
        url: str,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[dict], None]] = None
    ) -> str:
        """
        下载视频文件
        
        Args:
            url: 视频URL地址，支持YouTube、抖音、B站等平台
            output_dir: 输出目录，默认为配置的VIDEO_DOWNLOAD_DIR
            progress_callback: 进度回调函数，接收一个包含进度信息的字典
            
        Returns:
            str: 本地视频文件的绝对路径
            
        Raises:
            Exception: 下载失败时抛出异常
        """
        if output_dir is None:
            output_dir = self.download_dir
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置yt-dlp选项
        ydl_opts = {
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'progress_hooks': [self._progress_hook],
        }
        
        # 如果提供了自定义回调，添加到hooks中
        if progress_callback:
            ydl_opts['progress_hooks'].append(progress_callback)
        
        try:
            logger.info(f"Starting download from URL: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 提取视频信息
                info = ydl.extract_info(url, download=True)
                
                # 获取下载后的文件路径
                if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                    file_path = info['requested_downloads'][0].get('filepath')
                else:
                    # 兼容旧版本yt-dlp
                    file_path = ydl.prepare_filename(info)
                
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"Downloaded file not found: {file_path}")
                
                logger.info(f"Successfully downloaded video to: {file_path}")
                return file_path
                
        except Exception as e:
            logger.error(f"Failed to download video from {url}: {str(e)}")
            raise Exception(f"视频下载失败: {str(e)}") from e

    @staticmethod
    def _progress_hook(d: dict) -> None:
        """
        下载进度钩子函数
        
        Args:
            d: 进度信息字典，包含status、filename、downloaded_bytes等
        """
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes', 0)
            speed = d.get('speed', 0) or 0
            eta = d.get('eta', 0) or 0
            
            if total_bytes > 0:
                percent = (downloaded_bytes / total_bytes) * 100
                logger.debug(
                    f"Downloading: {percent:.1f}% - "
                    f"Speed: {speed / 1024 / 1024:.2f} MB/s - "
                    f"ETA: {eta}s"
                )
            else:
                logger.debug(
                    f"Downloading: {downloaded_bytes / 1024 / 1024:.2f} MB - "
                    f"Speed: {speed / 1024 / 1024:.2f} MB/s"
                )
                
        elif d['status'] == 'finished':
            filename = d.get('filename', 'unknown')
            logger.info(f"Download finished: {filename}")
            
        elif d['status'] == 'error':
            logger.error(f"Download error: {d.get('error', 'Unknown error')}")


def validate_video_url(url: str) -> bool:
    """
    验证视频URL是否有效
    
    Args:
        url: 待验证的URL
        
    Returns:
        bool: URL是否有效
    """
    from config import SUPPORTED_PLATFORMS
    
    # 简单的URL格式验证
    if not url.startswith(('http://', 'https://')):
        return False
    
    # 检查是否为支持的平台
    url_lower = url.lower()
    for platform in SUPPORTED_PLATFORMS:
        if platform in url_lower:
            return True
    
    # 如果没有匹配到已知平台，仍然允许尝试下载
    logger.warning(f"URL may not be from a supported platform: {url}")
    return True
