# Very Together User Service 部署指南

## 项目概述

这是一个基于Django的用户管理微服务，包含完整的认证授权、RBAC权限控制和审计日志功能。

## 系统要求

- Docker 20.0+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 2GB 可用磁盘空间

## 快速启动

### 1. 启动所有服务

```bash
# 一键启动（推荐）
./start.sh
```

或者手动启动：

```bash
# 启动所有服务
sudo docker-compose up -d

# 查看服务状态
docker-compose ps

# 运行数据库迁移
docker-compose exec user-service python manage.py migrate

# 创建超级管理员
docker-compose exec user-service python manage.py init_superuser

# 创建测试用户
docker-compose exec user-service python manage.py create_test_users
```

### 2. 停止所有服务

```bash
# 一键停止（推荐）
./stop.sh
```

或者手动停止：

```bash
sudo docker-compose down
```

## 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| API服务 | http://localhost:8001 | 主要API服务 |
| 健康检查 | http://localhost:8001/health/ | 服务健康状态 |
| API文档 | http://localhost:8001/docs/ | Swagger文档 |
| Nginx网关 | http://localhost | API网关入口 |
| PostgreSQL | localhost:5432 | 数据库服务 |
| Redis | localhost:6379 | 缓存服务 |
| Prometheus | http://localhost:9090 | 监控数据 |
| Grafana | http://localhost:3000 | 监控面板 |

## 默认账号

### 超级管理员
- **用户名**: admin
- **密码**: admin123
- **角色**: 系统根管理员

### 测试用户
创建脚本会自动创建以下测试用户：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| teacher01 | teacher123 | 教师 |
| student01 | student123 | 学生 |
| comp_admin | comp123 | 竞赛管理员 |

## API测试

```bash
# 运行API测试
./test_api.sh
```

## 主要API端点

### 认证相关
- `POST /api/v1/auth/login/` - 用户登录
- `POST /api/v1/auth/logout/` - 用户登出
- `POST /api/v1/auth/refresh/` - 刷新令牌
- `POST /api/v1/auth/change-password/` - 修改密码

### 用户管理
- `GET /api/v1/users/` - 获取用户列表
- `GET /api/v1/users/{id}/` - 获取用户详情
- `GET /api/v1/users/me/` - 获取当前用户信息
- `PATCH /api/v1/users/{id}/set_role/` - 更新用户角色
- `POST /api/v1/users/{id}/activate/` - 激活用户

### 活动审计
- `GET /api/v1/activities/` - 获取活动列表
- `GET /api/v1/activities/{id}/` - 获取活动详情

## 用户角色权限

| 角色 | 权限描述 |
|------|----------|
| super_admin | 系统超级管理员，拥有所有权限 |
| competition_admin | 学科竞赛管理员，可管理用户和竞赛 |
| teacher | 教师，可查看学生信息 |
| student | 学生，只能查看自己的信息 |

## 配置文件说明

### .env
环境变量配置文件，包含数据库连接、JWT密钥等配置。

### docker-compose.yml
Docker Compose配置文件，定义了所有微服务。

### Dockerfile
Docker镜像构建文件，已配置国内镜像源加速下载。

### config/nginx.conf
Nginx反向代理配置，包含API限流和安全配置。

### config/prometheus.yml
Prometheus监控配置。

## 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f user-service
docker-compose logs -f db
docker-compose logs -f redis

# 查看Nginx访问日志
docker-compose logs -f nginx
```

## 数据库管理

```bash
# 进入数据库容器
docker-compose exec db psql -U postgres -d user_service_db

# 备份数据库
docker-compose exec db pg_dump -U postgres user_service_db > backup.sql

# 恢复数据库
docker-compose exec -T db psql -U postgres user_service_db < backup.sql
```

## 故障排除

### 1. Docker权限问题
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER
# 重新登录或执行
newgrp docker
```

### 2. 端口冲突
如果端口被占用，修改docker-compose.yml中的端口映射。

### 3. 数据库连接失败
检查PostgreSQL容器是否正常运行：
```bash
docker-compose logs db
```

### 4. 内存不足
确保系统有足够内存运行所有容器，至少需要4GB。

### 5. 磁盘空间不足
清理Docker未使用的资源：
```bash
docker system prune -a
```

## 开发环境

如需在本地开发环境运行，可以：

1. 修改.env文件中的数据库配置为SQLite
2. 安装Python依赖：`pip install -r requirements/production.txt`
3. 运行迁移：`python manage.py migrate`
4. 启动服务：`python manage.py runserver 0.0.0.0:8001`

## 监控和告警

- **Prometheus**: 收集应用和系统指标
- **Grafana**: 可视化监控面板，默认账号admin/admin123
- **健康检查**: 自动检查服务状态

## 安全注意事项

1. 生产环境必须修改默认密钥和密码
2. 定期更新依赖包
3. 启用SSL/TLS加密
4. 配置防火墙规则
5. 定期备份数据库