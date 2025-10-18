# 依赖管理指南

本文档详细说明了 UserService 项目中使用的依赖管理策略和最佳实践。

## 概述

本项目使用 **pip-tools** 进行依赖管理，这是 Python 生态中推荐的依赖管理工具之一。pip-tools 提供了：

- ✅ 精确的版本锁定
- ✅ 依赖冲突检测
- ✅ 环境分离（开发/生产）
- ✅ 可重现的构建环境

## 文件结构

```
requirements/
├── base.in          # 基础依赖定义
├── base.txt         # 锁定的基础依赖版本
├── local.in         # 开发环境依赖定义
├── local.txt        # 锁定的开发依赖版本
├── production.in    # 生产环境依赖定义
└── production.txt   # 锁定的生产依赖版本
```

### 依赖文件说明

#### `requirements/base.in`
包含运行应用所需的核心依赖：
```ini
# Core Django
django>=5.2.7,<5.3.0

# Django REST Framework
djangorestframework>=3.16.1,<3.17.0

# Environment Variables
python-decouple>=3.8,<4.0.0

# CORS Support
django-cors-headers>=4.4.0,<4.5.0

# API Documentation
drf-spectacular>=0.27.2,<0.28.0

# Security
cryptography>=41.0.0

# HTTP Client for microservice communication
requests>=2.31.0,<3.0.0
httpx>=0.25.2,<0.26.0

# Validation and Serialization
marshmallow>=3.20.1,<4.0.0
```

#### `requirements/local.in`
包含开发、测试和代码质量工具：
```ini
-r base.in

# Database Drivers (for local development)
psycopg2-binary>=2.9.9,<3.0.0
mysqlclient>=2.2.4,<3.0.0

# Redis (for caching and sessions)
redis>=5.0.1,<6.0.0
django-redis>=5.4.0,<6.0.0

# Development Tools
django-debug-toolbar>=4.2.0,<4.3.0
django-extensions>=3.2.3,<4.0.0

# Code Quality
black>=23.0.0,<24.0.0
isort>=5.12.0,<6.0.0
flake8>=6.0.0,<7.0.0
mypy>=1.5.0,<2.0.0

# Testing
pytest>=7.4.3,<8.0.0
pytest-django>=4.7.0,<5.0.0
pytest-cov>=4.1.0,<5.0.0
factory-boy>=3.3.0,<4.0.0
faker>=20.1.0,<21.0.0
```

#### `requirements/production.in`
包含生产环境特定的依赖：
```ini
-r base.in

# Production Database Drivers
psycopg2-binary>=2.9.9,<3.0.0

# Redis (for production caching and sessions)
redis>=5.0.1,<6.0.0
django-redis>=5.4.0,<6.0.0

# Production Server
gunicorn>=21.2.0,<22.0.0
uvicorn>=0.24.0,<1.0.0

# Monitoring and Logging
structlog>=23.2.0,<24.0.0
sentry-sdk>=1.38.0,<2.0.0

# Background Tasks (if needed)
celery>=5.3.4,<6.0.0

# Security
django-environ>=0.11.0,<1.0.0

# Performance
django-storages>=1.14.0,<2.0.0

# Rate Limiting
django-ratelimit>=4.1.0,<5.0.0
```

## 工作流程

### 1. 初始设置

```bash
# 安装 pip-tools
pip install pip-tools

# 编译所有依赖文件
pip-compile requirements/base.in
pip-compile requirements/local.in
pip-compile requirements/production.in
```

### 2. 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements/local.txt
```

### 3. 生产环境部署

```bash
# 安装生产依赖
pip install -r requirements/production.txt
```

### 4. 添加新依赖

#### 添加基础依赖
```bash
# 编辑 requirements/base.in
echo "new-package>=1.0.0" >> requirements/base.in

# 重新编译
pip-compile requirements/base.in

# 这会自动更新 local.txt 和 production.txt
pip-compile requirements/local.in
pip-compile requirements/production.in
```

#### 添加开发依赖
```bash
# 编辑 requirements/local.in
echo "new-dev-package>=1.0.0" >> requirements/local.in

# 重新编译
pip-compile requirements/local.in
```

## 自动化脚本

项目提供了两个自动化脚本来简化依赖管理：

### `scripts/update_dependencies.sh`
更新所有依赖文件：

```bash
./scripts/update_dependencies.sh
```

该脚本会：
1. 检查并安装 pip-tools
2. 编译所有 .in 文件
3. 生成对应的 .txt 锁定文件
4. 显示后续操作指南

### `scripts/setup_dev.sh`
设置完整的开发环境：

```bash
./scripts/setup_dev.sh
```

该脚本会：
1. 创建虚拟环境
2. 安装 pip-tools
3. 安装开发依赖
4. 创建 .env 文件
5. 运行数据库迁移
6. 可选创建超级用户

## 最佳实践

### 1. 版本范围指定
```ini
# 推荐：指定合理的版本范围
django>=5.2.7,<5.3.0

# 避免：过于宽泛的版本范围
django>=5.0.0

# 避免：固定版本（除非必要）
django==5.2.7
```

### 2. 依赖分类
- **base.in**: 运行应用必需的依赖
- **local.in**: 开发、测试、代码质量工具
- **production.in**: 生产环境特定依赖

### 3. 定期更新
```bash
# 每月定期更新依赖
./scripts/update_dependencies.sh

# 检查安全更新
pip-audit
```

### 4. 版本锁定
- ✅ **.in 文件**：定义版本范围，可手动编辑
- ✅ **.txt 文件**：锁定精确版本，自动生成
- ❌ **不要手动编辑 .txt 文件**

### 5. 环境一致性
```bash
# 验证开发环境一致性
pip check

# 验证生产环境一致性
pip install -r requirements/production.txt
pip check
```

## 故障排除

### 依赖冲突
```bash
# 检查依赖冲突
pip check

# 查看依赖树
pip show <package-name>

# 强制重新编译
pip-compile requirements/base.in --rebuild
```

### 缓存问题
```bash
# 清理 pip 缓存
pip cache purge

# 重新编译
pip-compile requirements/base.in --no-cache
```

### 版本不匹配
```bash
# 查看可用版本
pip index versions <package-name>

# 更新特定依赖
pip-compile requirements/base.in --upgrade-package <package-name>
```

## 高级用法

### 1. 自定义索引
```bash
# 使用自定义 PyPI 索引
pip-compile requirements/base.in --index-url https://pypi.org/simple
```

### 2. 预发布版本
```bash
# 包含预发布版本
pip-compile requirements/base.in --pre
```

### 3. 最小版本
```bash
# 解析为最小兼容版本
pip-compile requirements/base.in --min
```

### 4. 生成哈希
```bash
# 生成包哈希值用于安全验证
pip-compile requirements/base.in --generate-hashes
```

## CI/CD 集成

### GitHub Actions 示例
```yaml
name: Dependencies Check

on: [push, pull_request]

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install pip-tools
      run: pip install pip-tools

    - name: Compile requirements
      run: |
        pip-compile requirements/base.in
        pip-compile requirements/local.in
        pip-compile requirements/production.in

    - name: Check for changes
      run: |
        git diff --exit-code || (
          echo "Requirements files are out of date. Run ./scripts/update_dependencies.sh"
          exit 1
        )
```

这种依赖管理策略确保了：
- 🎯 **可重现性**：相同依赖版本在不同环境中一致
- 🔒 **安全性**：锁定版本避免意外更新
- 🚀 **效率**：快速安装，无需解析依赖
- 🔧 **维护性**：清晰的依赖分类和版本控制