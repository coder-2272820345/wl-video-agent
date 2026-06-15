# AI视频创作Agent - PowerShell启动脚本
# 使用方法: .\start.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI视频创作Agent - 快速启动" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查.env文件是否存在
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  警告: .env文件不存在" -ForegroundColor Yellow
    Write-Host "📝 正在从.env.example创建.env文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ 已创建.env文件，请编辑该文件填入您的API Keys" -ForegroundColor Green
    Write-Host ""
    Read-Host "按回车键继续"
}

# 检查Docker是否安装
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: Docker未安装" -ForegroundColor Red
    Write-Host "请先安装Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# 检查docker-compose是否安装
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ docker-compose已安装: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: docker-compose未安装" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 选择启动模式
Write-Host "请选择启动模式:" -ForegroundColor Cyan
Write-Host "1) 完整模式（Web + Redis + 4个Worker）" -ForegroundColor White
Write-Host "2) 仅Web服务（需要本地运行Workers）" -ForegroundColor White
Write-Host "3) 带监控模式（Web + Redis + Workers + Flower）" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 启动完整模式..." -ForegroundColor Green
        docker-compose up -d
    }
    "2" {
        Write-Host ""
        Write-Host "🚀 仅启动Web服务和Redis..." -ForegroundColor Green
        docker-compose up -d redis web
        Write-Host ""
        Write-Host "💡 提示: 请在本地运行Celery Workers:" -ForegroundColor Yellow
        Write-Host "   celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing" -ForegroundColor Gray
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 启动带监控模式..." -ForegroundColor Green
        docker-compose --profile monitoring up -d
    }
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  服务启动中..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 等待服务启动
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host "📊 服务状态:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  访问地址" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🌐 Web界面: http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Green

if ($choice -eq "3") {
    Write-Host "🌸 Flower监控: http://localhost:5555 (admin/flower123)" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  常用命令" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "查看日志: docker-compose logs -f" -ForegroundColor White
Write-Host "停止服务: docker-compose down" -ForegroundColor White
Write-Host "重启服务: docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "🎉 启动完成！" -ForegroundColor Green
