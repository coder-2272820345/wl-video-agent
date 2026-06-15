#!/bin/bash
# AI视频创作Agent - 快速启动脚本（Linux/Mac）

echo "======================================"
echo "  AI视频创作Agent - 快速启动"
echo "======================================"
echo ""

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "⚠️  警告: .env文件不存在"
    echo "📝 正在从.env.example创建.env文件..."
    cp .env.example .env
    echo "✅ 已创建.env文件，请编辑该文件填入您的API Keys"
    echo ""
    read -p "按回车键继续..."
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: docker-compose未安装"
    echo "请先安装docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker和docker-compose已就绪"
echo ""

# 选择启动模式
echo "请选择启动模式:"
echo "1) 完整模式（Web + Redis + 4个Worker）"
echo "2) 仅Web服务（需要本地运行Workers）"
echo "3) 带监控模式（Web + Redis + Workers + Flower）"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动完整模式..."
        docker-compose up -d
        ;;
    2)
        echo ""
        echo "🚀 仅启动Web服务和Redis..."
        docker-compose up -d redis web
        echo ""
        echo "💡 提示: 请在本地运行Celery Workers:"
        echo "   celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing"
        ;;
    3)
        echo ""
        echo "🚀 启动带监控模式..."
        docker-compose --profile monitoring up -d
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "  服务启动中..."
echo "======================================"
echo ""

# 等待服务启动
sleep 5

# 检查服务状态
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "======================================"
echo "  访问地址"
echo "======================================"
echo "🌐 Web界面: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"

if [ "$choice" = "3" ]; then
    echo "🌸 Flower监控: http://localhost:5555 (admin/flower123)"
fi

echo ""
echo "======================================"
echo "  常用命令"
echo "======================================"
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
echo ""
echo "🎉 启动完成！"
