@echo off
chcp 65001 >nul
REM AI视频创作Agent - 快速启动脚本（Windows）
REM 使用方法: 在CMD中直接运行 start.bat
REM          或在PowerShell中运行 .\start.bat

echo ======================================
echo   AI视频创作Agent - 快速启动
echo ======================================
echo.

REM 检查.env文件是否存在
if not exist .env (
    echo ⚠️  警告: .env文件不存在
    echo 📝 正在从.env.example创建.env文件...
    copy .env.example .env
    echo ✅ 已创建.env文件，请编辑该文件填入您的API Keys
    echo.
    pause
)

REM 检查Docker是否安装
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM 检查docker-compose是否安装
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: docker-compose未安装
    pause
    exit /b 1
)

echo ✅ Docker和docker-compose已就绪
echo.

REM 选择启动模式
echo 请选择启动模式:
echo 1^) 完整模式（Web + Redis + 4个Worker）
echo 2^) 仅Web服务（需要本地运行Workers）
echo 3^) 带监控模式（Web + Redis + Workers + Flower）
echo.
set /p choice="请输入选项 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动完整模式...
    docker-compose up -d
) else if "%choice%"=="2" (
    echo.
    echo 🚀 仅启动Web服务和Redis...
    docker-compose up -d redis web
    echo.
    echo 💡 提示: 请在本地运行Celery Workers:
    echo    celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing
) else if "%choice%"=="3" (
    echo.
    echo 🚀 启动带监控模式...
    docker-compose --profile monitoring up -d
) else (
    echo ❌ 无效选项
    pause
    exit /b 1
)

echo.
echo ======================================
echo   服务启动中...
echo ======================================
echo.

REM 等待服务启动
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo 📊 服务状态:
docker-compose ps

echo.
echo ======================================
echo   访问地址
echo ======================================
echo 🌐 Web界面: http://localhost:8000
echo 📚 API文档: http://localhost:8000/docs

if "%choice%"=="3" (
    echo 🌸 Flower监控: http://localhost:5555 (admin/flower123)
)

echo.
echo ======================================
echo   常用命令
echo ======================================
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo 重启服务: docker-compose restart
echo.
echo 🎉 启动完成！
pause
