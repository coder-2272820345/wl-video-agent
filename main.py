"""
AI视频创作Agent - FastAPI主入口
提供视频下载、脚本生成、语音合成、视频生成等功能的REST API
"""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from celery.result import AsyncResult
import uuid
from pathlib import Path

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from downloader import VideoDownloader, validate_video_url

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI视频创作Agent",
    description="自动化视频创作全流程服务",
    version="1.0.0"
)

# 配置静态文件和模板
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 初始化Celery（这里先占位，后续会完善）
from celery import Celery
celery_app = Celery(
    'video_agent',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# 初始化下载器
video_downloader = VideoDownloader()


# ==================== Pydantic模型 ====================

class DownloadRequest(BaseModel):
    """视频下载请求模型"""
    url: str = Field(..., description="视频URL地址", example="https://www.youtube.com/watch?v=example")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: Optional[str] = Field(None, description="附加消息")


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: PENDING/RUNNING/SUCCESS/FAILURE")
    result: Optional[dict] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")


# ==================== API路由 ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径，返回Web界面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download", response_model=TaskResponse)
async def download_video(request: DownloadRequest):
    """
    下载视频接口
    
    接收视频URL，异步调用下载模块，返回任务ID
    
    Args:
        request: 包含视频URL的请求体
        
    Returns:
        TaskResponse: 包含任务ID和状态的响应
        
    Raises:
        HTTPException: 当URL无效或任务提交失败时抛出
    """
    # 验证URL格式
    if not validate_video_url(request.url):
        raise HTTPException(status_code=400, detail="无效的视频URL")
    
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 异步执行下载任务
        task = download_video_task.delay(request.url, task_id)
        
        logger.info(f"Download task submitted: {task_id} for URL: {request.url}")
        
        return TaskResponse(
            task_id=task_id,
            status="PENDING",
            message="视频下载任务已提交"
        )
        
    except Exception as e:
        logger.error(f"Failed to submit download task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    查询任务状态接口
    
    Args:
        task_id: 任务ID
        
    Returns:
        TaskStatus: 任务状态信息
        
    Raises:
        HTTPException: 当任务不存在时抛出
    """
    try:
        # 查询Celery任务状态
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return TaskStatus(
                task_id=task_id,
                status="PENDING",
                message="任务等待中"
            )
        elif task_result.state == 'STARTED':
            return TaskStatus(
                task_id=task_id,
                status="RUNNING",
                message="任务执行中"
            )
        elif task_result.state == 'SUCCESS':
            return TaskStatus(
                task_id=task_id,
                status="SUCCESS",
                result=task_result.result
            )
        elif task_result.state == 'FAILURE':
            return TaskStatus(
                task_id=task_id,
                status="FAILURE",
                error=str(task_result.result)
            )
        else:
            return TaskStatus(
                task_id=task_id,
                status=task_result.state
            )
            
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


# ==================== Celery任务（临时占位） ====================

@celery_app.task(bind=True, name='download_video_task')
def download_video_task(self, url: str, task_id: str) -> dict:
    """
    视频下载Celery任务
    
    Args:
        url: 视频URL
        task_id: 任务ID
        
    Returns:
        dict: 包含下载结果的信息
    """
    try:
        logger.info(f"Starting download task {task_id} for URL: {url}")
        
        # 调用下载器
        file_path = video_downloader.download(url)
        
        logger.info(f"Download task {task_id} completed successfully")
        
        return {
            "task_id": task_id,
            "file_path": str(file_path),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Download task {task_id} failed: {str(e)}")
        raise Exception(f"下载失败: {str(e)}") from e


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Video Agent API server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
