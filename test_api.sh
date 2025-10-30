#!/bin/bash

echo "=== Very Together User Service API 测试脚本 ==="

API_BASE="http://localhost:8001/api/v1"

# 检查服务是否运行
echo "🔍 检查服务状态..."
if ! curl -s http://localhost:8001/health/ > /dev/null; then
    echo "❌ 服务未运行，请先启动服务: ./start.sh"
    exit 1
fi

echo "✅ 服务运行正常"
echo ""

# 健康检查
echo "📊 健康检查:"
curl -s http://localhost:8001/health/ | python3 -m json.tool || echo "健康检查失败"
echo ""

# 登录测试
echo "🔐 测试用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"userid": "admin", "password": "admin123"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool || echo "登录失败"

# 提取token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except:
    pass
")

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ 登录成功，获取到访问令牌"
    echo ""

    # 获取当前用户信息
    echo "👤 获取当前用户信息:"
    curl -s -X GET "$API_BASE/users/me/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool || echo "获取用户信息失败"
    echo ""

    # 获取用户列表
    echo "👥 获取用户列表:"
    curl -s -X GET "$API_BASE/users/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool || echo "获取用户列表失败"
    echo ""

    # 获取活动列表
    echo "📋 获取用户活动列表:"
    curl -s -X GET "$API_BASE/activities/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool || echo "获取活动列表失败"
    echo ""

else
    echo "❌ 登录失败，无法获取访问令牌"
fi

echo "🎉 API 测试完成！"