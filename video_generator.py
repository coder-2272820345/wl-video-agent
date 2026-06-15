"""
视频生成模块
使用可灵API或通义万相生成口播视频
"""
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from config import KLING_ACCESS_KEY, DASHSCOPE_API_KEY, OUTPUT_DIR

logger = logging.getLogger(__name__)


class VideoGenerator:
    """视频生成器类"""

    def __init__(self):
        """初始化VideoGenerator"""
        self.output_dir = OUTPUT_DIR
        logger.info(f"VideoGenerator initialized with output dir: {self.output_dir}")

    def image_to_video(
        self,
        image_url: str,
        audio_url: str,
        prompt: str,
        provider: str = "kling",
        duration: int = 10
    ) -> str:
        """
        根据图像和音频生成口播视频
        
        Args:
            image_url: 角色图像URL或本地路径
            audio_url: 音频文件URL或本地路径
            prompt: 动作描述提示词
            provider: 使用的提供商，'kling'（可灵）或 'tongyi'（通义万相）
            duration: 视频时长（秒）
            
        Returns:
            str: 生成的视频文件路径或URL
            
        Raises:
            Exception: 视频生成失败时抛出异常
        """
        if not image_url or not audio_url:
            raise ValueError("图像和音频URL不能为空")
        
        try:
            logger.info(f"Generating video from image and audio using {provider}")
            
            if provider == "kling":
                return self._generate_with_kling(image_url, audio_url, prompt, duration)
            elif provider == "tongyi":
                return self._generate_with_tongyi(image_url, audio_url, prompt, duration)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to generate video: {str(e)}")
            raise Exception(f"视频生成失败: {str(e)}") from e

    def _generate_with_kling(
        self,
        image_url: str,
        audio_url: str,
        prompt: str,
        duration: int
    ) -> str:
        """
        使用可灵API生成视频
        
        Args:
            image_url: 图像URL
            audio_url: 音频URL
            prompt: 动作描述
            duration: 视频时长
            
        Returns:
            str: 生成的视频URL
            
        Raises:
            Exception: 可灵API调用失败
        """
        try:
            import requests
            
            # 可灵API端点
            api_url = "https://api.klingai.com/v1/videos/image-to-video"
            
            headers = {
                "Authorization": f"Bearer {KLING_ACCESS_KEY}",
                "Content-Type": "application/json"
            }
            
            # 构建请求数据
            data = {
                "image_url": image_url,
                "prompt": prompt,
                "duration": duration,
                "audio_url": audio_url
            }
            
            # 发送请求
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                
                if not task_id:
                    raise Exception("No task_id in response")
                
                logger.info(f"Kling video generation task created: {task_id}")
                
                # 轮询查询任务状态
                video_url = self._poll_kling_task_status(task_id)
                
                if video_url:
                    logger.info(f"Kling generated video: {video_url}")
                    return video_url
                else:
                    raise Exception("Video generation timed out")
            else:
                raise Exception(f"Kling API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Kling API error: {str(e)}")
            raise Exception(f"可灵视频生成失败: {str(e)}") from e

    def _poll_kling_task_status(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        """
        轮询可灵任务状态
        
        Args:
            task_id: 任务ID
            max_wait: 最大等待时间（秒）
            
        Returns:
            Optional[str]: 视频URL，超时返回None
        """
        import requests
        
        api_url = f"https://api.klingai.com/v1/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {KLING_ACCESS_KEY}"
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(api_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'completed':
                        return result.get('video_url')
                    elif status in ['failed', 'error']:
                        raise Exception(f"Task failed: {result.get('error_message')}")
                    elif status in ['pending', 'processing']:
                        logger.info(f"Task {task_id} is {status}, waiting...")
                        time.sleep(10)  # 每10秒查询一次
                    else:
                        logger.warning(f"Unknown task status: {status}")
                        time.sleep(10)
                else:
                    logger.error(f"Failed to query task status: {response.status_code}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"Error polling task status: {str(e)}")
                time.sleep(10)
        
        logger.warning(f"Task {task_id} timed out after {max_wait} seconds")
        return None

    def _generate_with_tongyi(
        self,
        image_url: str,
        audio_url: str,
        prompt: str,
        duration: int
    ) -> str:
        """
        使用通义万相生成视频
        
        Args:
            image_url: 图像URL
            audio_url: 音频URL
            prompt: 动作描述
            duration: 视频时长
            
        Returns:
            str: 生成的视频URL
            
        Raises:
            Exception: 通义万相API调用失败
        """
        try:
            import dashscope
            from dashscope import VideoSynthesis
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            # 构建提示词
            full_prompt = f"{prompt}，自然流畅的动作，高质量视频"
            
            # 调用通义万相视频生成API
            response = VideoSynthesis.call(
                model='wanx-v1-video',
                image_url=image_url,
                prompt=full_prompt,
                duration=duration
            )
            
            if response.status_code == 200:
                # 获取任务ID并轮询
                task_id = response.output.task_id
                
                logger.info(f"Tongyi video generation task created: {task_id}")
                
                # 轮询查询结果
                video_url = self._poll_tongyi_task_status(task_id)
                
                if video_url:
                    logger.info(f"Tongyi generated video: {video_url}")
                    return video_url
                else:
                    raise Exception("Video generation timed out")
            else:
                raise Exception(f"Tongyi Wanxiang API error: {response.message}")
                
        except ImportError:
            raise Exception("dashscope package not installed")
        except Exception as e:
            logger.error(f"Tongyi Wanxiang video error: {str(e)}")
            raise Exception(f"通义万相视频生成失败: {str(e)}") from e

    def _poll_tongyi_task_status(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        """
        轮询通义万相任务状态
        
        Args:
            task_id: 任务ID
            max_wait: 最大等待时间（秒）
            
        Returns:
            Optional[str]: 视频URL，超时返回None
        """
        try:
            import dashscope
            from dashscope import VideoSynthesis
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # 查询任务状态
                    response = VideoSynthesis.fetch(task_id=task_id)
                    
                    if response.status_code == 200:
                        status = response.output.task_status
                        
                        if status == 'SUCCEEDED':
                            return response.output.video_url
                        elif status in ['FAILED', 'UNKNOWN']:
                            raise Exception(f"Task failed: {response.output.message}")
                        elif status in ['PENDING', 'RUNNING']:
                            logger.info(f"Task {task_id} is {status}, waiting...")
                            time.sleep(15)  # 每15秒查询一次
                        else:
                            logger.warning(f"Unknown task status: {status}")
                            time.sleep(15)
                    else:
                        logger.error(f"Failed to query task status: {response.message}")
                        time.sleep(15)
                        
                except Exception as e:
                    logger.error(f"Error polling task status: {str(e)}")
                    time.sleep(15)
            
            logger.warning(f"Task {task_id} timed out after {max_wait} seconds")
            return None
            
        except Exception as e:
            logger.error(f"Tongyi task polling error: {str(e)}")
            return None
