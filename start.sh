#!/bin/bash

echo "=== Very Together User Service 启动脚本 ==="

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "❌ .env文件不存在，正在从模板创建..."
    cp .env.example .env
    echo "✅ 已创建.env文件，请根据需要修改配置"
fi

# 检查Docker权限
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker权限不足，请使用以下命令添加用户到docker组："
    echo "   sudo usermod -aG docker \$USER"
    echo "   然后重新登录或执行: newgrp docker"
    exit 1
fi

echo "✅ Docker权限检查通过"

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 清理并重新构建镜像
echo "🧹 清理旧镜像并重新构建..."
docker-compose build --no-cache

# 构建并启动服务
echo "🚀 启动Docker Compose服务..."
docker-compose up -d

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 15

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 等待User Service启动
echo "⏳ 等待User Service启动..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health/ > /dev/null 2>&1; then
        echo "✅ User Service已启动"
        break
    fi
    echo "等待User Service启动... ($i/30)"
    sleep 2
done

# 运行数据库迁移
echo "🗄️ 运行数据库迁移..."
docker-compose exec -T user-service python manage.py migrate || echo "⚠️ 数据库迁移失败，请检查日志"

# 创建超级管理员
echo "👤 创建超级管理员..."
docker-compose exec -T user-service python manage.py init_superuser || echo "⚠️ 超级管理员创建失败，请检查日志"

# 创建测试用户
echo "👥 创建测试用户..."
docker-compose exec -T user-service python manage.py create_test_users || echo "⚠️ 测试用户创建失败，请检查日志"

# 最后测试服务访问
echo "🧪 测试服务访问..."
echo "测试直接访问User Service:"
if curl -s http://localhost:8001/health/ > /dev/null; then
    echo "✅ User Service (8001端口) - 可访问"
else
    echo "❌ User Service (8001端口) - 无法访问"
fi

echo "测试通过Nginx网关访问:"
if curl -s http://localhost/health/ > /dev/null; then
    echo "✅ Nginx网关 (80端口) - 可访问"
else
    echo "❌ Nginx网关 (80端口) - 无法访问"
fi

echo ""
echo "🎉 服务启动完成！"
echo ""
echo "📋 服务访问地址："
echo "   - User Service (直接): http://localhost:8001"
echo "   - User Service (网关):  http://localhost"
echo "   - 健康检查:           http://localhost:8001/health/ 或 http://localhost/health/"
echo "   - API文档:            http://localhost:8001/docs/ 或 http://localhost/docs/"
echo "   - PostgreSQL:         localhost:5432"
echo "   - Redis:              localhost:6379"
echo "   - Prometheus:         http://localhost:9090"
echo "   - Grafana:            http://localhost:3000 (admin/admin123)"
echo ""
echo "🔍 如果服务无法访问，请运行: ./check_services.sh"
echo "🔑 默认超级管理员账号："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "📝 查看日志:"
echo "   docker-compose logs -f user-service"
echo ""