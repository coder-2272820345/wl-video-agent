"""
Celery配置文件
定义任务队列、重试策略等高级配置
"""
from celery import Celery
from celery.schedules import crontab
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# 创建Celery应用
celery_app = Celery(
    'video_agent',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# ==================== Celery基础配置 ====================
celery_app.conf.update(
    # 序列化配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区配置
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务追踪
    task_track_started=True,
    
    # 任务超时配置
    task_time_limit=3600,  # 1小时硬超时
    task_soft_time_limit=3000,  # 50分钟软超时
    
    # 任务结果配置
    task_result_expires=86400,  # 结果保留24小时
    
    # Worker配置
    worker_prefetch_multiplier=1,  # 每次只预取一个任务
    worker_max_tasks_per_child=100,  # 每个worker处理100个任务后重启
    
    # 任务路由配置
    task_routes={
        'download_video_task': {'queue': 'download'},
        'analyze_and_generate_script': {'queue': 'analysis'},
        'generate_video_from_script': {'queue': 'generation'},
        'compose_final_video': {'queue': 'editing'},
    },
    
    # 任务优先级
    task_priority=0,
    
    # ACKS配置
    task_acks_late=True,  # 任务完成后才确认
    task_acks_on_failure_or_timeout=True,
    
    # 速率限制（可选）
    # task_annotations={
    #     'download_video_task': {'rate_limit': '10/m'},
    # },
)

# ==================== 定时任务配置（可选）====================
celery_app.conf.beat_schedule = {
    # 每天凌晨清理临时文件
    'cleanup-temp-files': {
        'task': 'cleanup_temp_files',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
}

# ==================== 错误处理配置 ====================
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.broker_connection_retry_on_startup = True

# ==================== 日志配置 ====================
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_log_format = (
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
celery_app.conf.worker_task_log_format = (
    '%(asctime)s - %(name)s - %(levelname)s - [%(task_name)s(%(task_id)s)] - %(message)s'
)


# ==================== 启动命令示例 ====================
"""
启动Worker（不同队列）:
- 下载队列: celery -A celery_config.celery_app worker --loglevel=info -Q download -n worker_download@%h
- 分析队列: celery -A celery_config.celery_app worker --loglevel=info -Q analysis -n worker_analysis@%h
- 生成队列: celery -A celery_config.celery_app worker --loglevel=info -Q generation -n worker_generation@%h
- 剪辑队列: celery -A celery_config.celery_app worker --loglevel=info -Q editing -n worker_editing@%h

启动所有队列的Worker:
- celery -A celery_config.celery_app worker --loglevel=info -Q download,analysis,generation,editing

启动Beat（定时任务）:
- celery -A celery_config.celery_app beat --loglevel=info

监控工具(Flower):
- pip install flower
- celery -A celery_config.celery_app flower --port=5555
"""
