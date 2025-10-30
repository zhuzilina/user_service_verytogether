#!/bin/bash

echo "=== Very Together User Service 服务检查脚本 ==="

# 检查Docker权限
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker权限不足，请使用sudo运行或添加用户到docker组"
    exit 1
fi

echo "🔍 检查服务状态..."
echo ""

# 检查容器状态
echo "📦 Docker容器状态:"
docker-compose ps
echo ""

# 检查端口占用
echo "🔌 端口占用情况:"
echo "端口 80 (Nginx):"
netstat -tlnp | grep :80 || echo "未监听端口80"
echo ""
echo "端口 8001 (User Service):"
netstat -tlnp | grep :8001 || echo "未监听端口8001"
echo ""

# 测试各个访问点
echo "🌐 测试服务访问:"

echo "1. 测试直接访问User Service (8001端口):"
if curl -s --connect-timeout 5 http://localhost:8001/health/ > /dev/null; then
    echo "   ✅ http://localhost:8001/health/ - 可访问"
    curl -s http://localhost:8001/health/ | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health/
else
    echo "   ❌ http://localhost:8001/health/ - 无法访问"
fi
echo ""

echo "2. 测试通过Nginx网关访问 (80端口):"
if curl -s --connect-timeout 5 http://localhost/health/ > /dev/null; then
    echo "   ✅ http://localhost/health/ - 可访问"
    curl -s http://localhost/health/ | python3 -m json.tool 2>/dev/null || curl -s http://localhost/health/
else
    echo "   ❌ http://localhost/health/ - 无法访问"
fi
echo ""

echo "3. 测试API端点:"
if curl -s --connect-timeout 5 http://localhost/api/v1/health/ > /dev/null; then
    echo "   ✅ http://localhost/api/v1/ - 可访问"
else
    echo "   ❌ http://localhost/api/v1/ - 无法访问"
fi
echo ""

# 检查容器日志
echo "📋 查看服务日志 (最后20行):"
echo "User Service日志:"
docker-compose logs --tail=20 user-service 2>/dev/null || echo "无法获取user-service日志"
echo ""

echo "Nginx日志:"
docker-compose logs --tail=10 nginx 2>/dev/null || echo "无法获取nginx日志"
echo ""

echo "🔧 故障排除建议:"
echo "1. 如果User Service容器未运行: docker-compose up -d user-service"
echo "2. 如果Nginx容器未运行: docker-compose up -d nginx"
echo "3. 如果端口被占用: sudo lsof -i :80 或 sudo lsof -i :8001"
echo "4. 重启所有服务: ./stop.sh && ./start.sh"
echo "5. 查看完整日志: docker-compose logs -f"