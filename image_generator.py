"""
图像生成模块
使用通义万相或腾讯云生成角色图像
"""
import logging
import uuid
from pathlib import Path
from typing import Optional

from config import DASHSCOPE_API_KEY, TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TEMP_DIR

logger = logging.getLogger(__name__)


class ImageGenerator:
    """图像生成器类"""

    def __init__(self):
        """初始化ImageGenerator"""
        self.temp_dir = TEMP_DIR
        logger.info(f"ImageGenerator initialized with temp dir: {self.temp_dir}")

    def generate_character(
        self,
        description: str,
        output_path: Optional[str] = None,
        provider: str = "tongyi"
    ) -> str:
        """
        生成角色图像
        
        Args:
            description: 角色描述文本
            output_path: 输出图像路径，默认自动生成
            provider: 使用的提供商，'tongyi'（通义万相）或 'tencent'（腾讯云）
            
        Returns:
            str: 生成的图像文件路径
            
        Raises:
            Exception: 图像生成失败时抛出异常
        """
        if not description or len(description.strip()) < 5:
            raise ValueError("角色描述不能为空或过短")
        
        # 如果没有指定输出路径，自动生成
        if output_path is None:
            image_filename = f"character_{uuid.uuid4().hex[:8]}.png"
            output_path = str(self.temp_dir / image_filename)
        
        try:
            logger.info(f"Generating character image: {description}")
            
            if provider == "tongyi":
                return self._generate_with_tongyi(description, output_path)
            elif provider == "tencent":
                return self._generate_with_tencent(description, output_path)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to generate character image: {str(e)}")
            raise Exception(f"角色图像生成失败: {str(e)}") from e

    def _generate_with_tongyi(self, description: str, output_path: str) -> str:
        """
        使用通义万相生成图像
        
        Args:
            description: 角色描述
            output_path: 输出路径
            
        Returns:
            str: 图像文件路径
            
        Raises:
            Exception: 通义万相调用失败
        """
        try:
            import dashscope
            from dashscope import ImageSynthesis
            
            dashscope.api_key = DASHSCOPE_API_KEY
            
            # 构建提示词
            prompt = f"高质量角色设计图，{description}，精美细节，专业插画风格"
            
            # 调用通义万相API
            response = ImageSynthesis.call(
                model='wanx-v1',
                prompt=prompt,
                n=1,
                size='1024*1024'
            )
            
            if response.status_code == 200:
                # 获取图像URL
                image_url = response.output.results[0].url
                
                # 下载图像到本地
                import requests
                img_response = requests.get(image_url, timeout=30)
                
                if img_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    logger.info(f"Tongyi Wanxiang generated image: {output_path}")
                    return output_path
                else:
                    raise Exception("Failed to download generated image")
            else:
                raise Exception(f"Tongyi Wanxiang API error: {response.message}")
                
        except ImportError:
            raise Exception("dashscope package not installed")
        except Exception as e:
            logger.error(f"Tongyi Wanxiang error: {str(e)}")
            raise Exception(f"通义万相生成失败: {str(e)}") from e

    def _generate_with_tencent(self, description: str, output_path: str) -> str:
        """
        使用腾讯云HY-Image-V3.0生成图像
        
        Args:
            description: 角色描述
            output_path: 输出路径
            
        Returns:
            str: 图像文件路径
            
        Raises:
            Exception: 腾讯云API调用失败
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
            import json
            
            # 创建认证对象
            cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
            
            # 配置HTTP选项
            httpProfile = HttpProfile()
            httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
            
            # 配置客户端选项
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # 创建客户端
            client = hunyuan_client.HunyuanClient(cred, "", clientProfile)
            
            # 构建请求
            req = models.TextToImageLiteRequest()
            params = {
                "Prompt": f"角色设计，{description}，高质量，精美细节",
                "Resolution": "1024:1024",
                "Style": 1  # 默认风格
            }
            req.from_json_string(json.dumps(params))
            
            # 发送请求
            resp = client.TextToImageLite(req)
            
            # 解析响应
            result = json.loads(resp.to_json_string())
            image_url = result.get('ImageUrl', '')
            
            if image_url:
                # 下载图像到本地
                import requests
                img_response = requests.get(image_url, timeout=30)
                
                if img_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    logger.info(f"Tencent HY-Image generated image: {output_path}")
                    return output_path
                else:
                    raise Exception("Failed to download generated image")
            else:
                raise Exception("No image URL in response")
                
        except ImportError:
            raise Exception("tencentcloud-sdk-python package not installed")
        except Exception as e:
            logger.error(f"Tencent HY-Image error: {str(e)}")
            raise Exception(f"腾讯云图像生成失败: {str(e)}") from e
