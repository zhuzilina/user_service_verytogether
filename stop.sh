#!/bin/bash

echo "=== Very Together User Service 停止脚本 ==="

# 检查Docker权限
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker权限不足"
    exit 1
fi

echo "✅ Docker权限检查通过"

# 停止所有服务
echo "🛑 停止所有服务..."
docker-compose down

# 清理未使用的容器和网络
echo "🧹 清理未使用的资源..."
docker system prune -f

echo "✅ 所有服务已停止！"