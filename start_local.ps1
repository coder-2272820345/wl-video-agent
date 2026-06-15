# AI视频创作Agent - 本地启动脚本（无需Docker）
# 使用方法: .\start_local.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI视频创作Agent - 本地启动" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: Python未安装" -ForegroundColor Red
    Write-Host "请安装Python 3.10+: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 检查pip
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: pip未安装" -ForegroundColor Red
    exit 1
}

# 检查FFmpeg
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✅ FFmpeg已安装" -ForegroundColor Green
} catch {
    Write-Host "⚠️  警告: FFmpeg未找到" -ForegroundColor Yellow
    Write-Host "请下载FFmpeg: https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "并添加到系统PATH" -ForegroundColor Yellow
    $continue = Read-Host "是否继续? (y/n)"
    if ($continue -ne "y") { exit 1 }
}

# 检查.env文件
if (-Not (Test-Path ".env")) {
    Write-Host "📝 正在从.env.example创建.env文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ 已创建.env文件" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  启动选项" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1) 完整启动（Redis + Workers + Web）" -ForegroundColor White
Write-Host "2) 仅启动Web服务（需要手动启动Redis和Workers）" -ForegroundColor White
Write-Host "3) 仅启动Workers（需要手动启动Redis和Web）" -ForegroundColor White
Write-Host "4) 安装依赖" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1/2/3/4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 完整启动模式" -ForegroundColor Green
        Write-Host ""
        
        # 检查Redis是否运行
        Write-Host "检查Redis连接..." -ForegroundColor Yellow
        try {
            $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
            if ($redisTest.TcpTestSucceeded) {
                Write-Host "✅ Redis已运行" -ForegroundColor Green
            } else {
                Write-Host "❌ Redis未运行" -ForegroundColor Red
                Write-Host "请先启动Redis服务器" -ForegroundColor Yellow
                Write-Host "- Windows: 运行 redis-server.exe" -ForegroundColor Gray
                Write-Host "- Docker: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Gray
                exit 1
            }
        } catch {
            Write-Host "❌ 无法连接到Redis" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "提示: 将在新窗口中启动Workers和Web服务" -ForegroundColor Cyan
        Write-Host ""
        
        # 启动Workers
        Write-Host "启动Celery Workers..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing"
        
        Start-Sleep -Seconds 2
        
        # 启动Web服务
        Write-Host "启动Web服务..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python main.py"
        
        Start-Sleep -Seconds 3
        
        Write-Host ""
        Write-Host "======================================" -ForegroundColor Cyan
        Write-Host "  服务已启动" -ForegroundColor Cyan
        Write-Host "======================================" -ForegroundColor Cyan
        Write-Host "🌐 Web界面: http://localhost:8000" -ForegroundColor Green
        Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host ""
        Write-Host "查看Workers窗口了解任务执行状态" -ForegroundColor Yellow
    }
    
    "2" {
        Write-Host ""
        Write-Host "🚀 启动Web服务..." -ForegroundColor Green
        python main.py
    }
    
    "3" {
        Write-Host ""
        Write-Host "🚀 启动Celery Workers..." -ForegroundColor Green
        celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing
    }
    
    "4" {
        Write-Host ""
        Write-Host "📦 安装Python依赖..." -ForegroundColor Green
        pip install -r requirements.txt
        Write-Host ""
        Write-Host "✅ 依赖安装完成" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  常用命令" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "安装依赖: pip install -r requirements.txt" -ForegroundColor White
Write-Host "启动Redis: redis-server (Windows) 或 docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor White
Write-Host "启动Workers: celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing" -ForegroundColor White
Write-Host "启动Web: python main.py" -ForegroundColor White
Write-Host ""
