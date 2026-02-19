# GPT-Researcher 本地服务器部署规划指南

## 目录

1. [架构概述](#架构概述)
2. [硬件需求规划](#硬件需求规划)
3. [部署方案选择](#部署方案选择)
4. [环境配置详解](#环境配置详解)
5. [API 密钥与成本规划](#api-密钥与成本规划)
6. [安全配置](#安全配置)
7. [监控与运维](#监控与运维)
8. [扩展与优化](#扩展与优化)
9. [常见问题解决](#常见问题解决)

---

## 架构概述

### 系统组件

```
┌─────────────────────────────────────────────────────────────┐
│                    用户访问层                                 │
│                   (浏览器 / API)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx 反向代理                             │
│              (端口 3000 - 统一入口)                           │
│   ┌─────────────────┬──────────────────┬─────────────────┐  │
│   │  /ws, /outputs  │  /reports        │  其他路径        │  │
│   │  → Backend      │  → Backend       │  → Frontend     │  │
│   └─────────────────┴──────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│    FastAPI Backend      │     │    Next.js Frontend     │
│    (端口 8000)          │     │    (端口 3001 内部)     │
│                         │     │                         │
│  • WebSocket 通信       │     │  • 用户界面             │
│  • 研究任务处理         │     │  • 报告展示             │
│  • 报告生成             │     │  • 交互控制             │
└─────────────────────────┘     └─────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    外部服务依赖                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  LLM API     │  │  搜索 API    │  │  爬虫服务    │       │
│  │  (OpenAI/    │  │  (Tavily/    │  │  (Selenium/  │       │
│  │   Ollama)    │  │   DuckDuckGo)│  │   Playwright)│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 项目提供的 Docker 镜像

| 镜像名称 | 用途 | 端口 |
|---------|------|------|
| `gptresearcher/gpt-researcher` | 后端 API 服务 | 8000 |
| `gptresearcher/gptr-nextjs` | 前端 Web 界面 | 3000 |
| `Dockerfile.fullstack` | 一体化全栈部署 | 3000, 8000 |

---

## 硬件需求规划

### 最低配置（小规模/测试环境）

| 组件 | 规格 | 说明 |
|------|------|------|
| CPU | 2 核 | 基础处理能力 |
| 内存 | 4 GB | 运行 Python + Node.js |
| 存储 | 20 GB SSD | 系统 + Docker 镜像 + 日志 |
| 网络 | 10 Mbps | 需要访问外部 API |

### 推荐配置（生产环境）

| 组件 | 规格 | 说明 |
|------|------|------|
| CPU | 4-8 核 | 支持并发研究任务 |
| 内存 | 8-16 GB | 处理大型文档和爬虫 |
| 存储 | 100 GB SSD | 报告存储 + 日志 + 本地文档 |
| 网络 | 100 Mbps+ | 快速爬取网页内容 |

### 高性能配置（本地 LLM 部署）

如果计划使用 Ollama 运行本地模型：

| 组件 | 规格 | 说明 |
|------|------|------|
| CPU | 8+ 核 | 模型推理加速 |
| 内存 | 32 GB+ | 加载大型语言模型 |
| GPU | NVIDIA RTX 3090/4090 或 A100 | 显存 24GB+ |
| 存储 | 500 GB NVMe SSD | 模型文件 + 数据 |

### 内存估算

```
基础服务占用:
├── Python FastAPI 后端:     ~500 MB - 1 GB
├── Node.js 前端:            ~200 MB - 500 MB
├── Nginx:                   ~50 MB
├── Chromium (爬虫):         ~200 MB - 1 GB (每个实例)
└── 系统开销:                ~500 MB

单次研究任务:
├── 普通研究 (research_report):  ~500 MB 额外
├── 详细研究 (detailed_report):  ~1 GB 额外
└── 深度研究 (deep):            ~2-4 GB 额外

本地 LLM (可选):
├── Llama 3 8B:              ~8 GB VRAM
├── Llama 3 70B:             ~40 GB VRAM (需要量化)
└── Qwen 7B:                 ~7 GB VRAM
```

---

## 部署方案选择

### 方案 A：Docker Compose（推荐）

最简单的部署方式，适合大多数场景。

#### 步骤 1：准备环境

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin
```

#### 步骤 2：克隆项目

```bash
git clone https://github.com/assafelovic/gpt-researcher.git
cd gpt-researcher
```

#### 步骤 3：配置环境变量

```bash
cp .env.example .env
nano .env
```

编辑 `.env` 文件：

```bash
# 必需的 API 密钥
OPENAI_API_KEY=sk-your-openai-key
TAVILY_API_KEY=tvly-your-tavily-key

# 可选：使用其他 LLM 提供商
# OPENAI_BASE_URL=https://api.openai.com/v1

# 本地文档路径
DOC_PATH=./my-docs

# 前端 API 地址（根据服务器 IP 修改）
NEXT_PUBLIC_GPTR_API_URL=http://your-server-ip:8000
```

#### 步骤 4：启动服务

```bash
# 构建并启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f
```

#### 步骤 5：验证部署

```bash
# 检查服务状态
docker compose ps

# 测试后端 API
curl http://localhost:8000/

# 访问前端
# 打开浏览器访问 http://your-server-ip:3000
```

---

### 方案 B：全栈单容器部署

使用 `Dockerfile.fullstack`，所有服务运行在一个容器内。

```bash
# 构建镜像
docker build -f Dockerfile.fullstack -t gpt-researcher-fullstack .

# 运行容器
docker run -d \
  --name gpt-researcher \
  -p 3000:3000 \
  -p 8000:8000 \
  -v $(pwd)/my-docs:/usr/src/app/my-docs \
  -v $(pwd)/outputs:/usr/src/app/outputs \
  -e OPENAI_API_KEY=sk-your-key \
  -e TAVILY_API_KEY=tvly-your-key \
  gpt-researcher-fullstack
```

优点：
- 单一容器管理
- 内置 Nginx 反向代理
- 适合简单部署

缺点：
- 无法独立扩展组件
- 调试相对困难

---

### 方案 C：原生部署（不使用 Docker）

适合需要深度定制或在特殊环境运行的场景。

#### 系统依赖安装

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  python3.12 python3.12-venv python3-pip \
  nodejs npm \
  chromium-browser chromium-chromedriver \
  firefox-esr \
  nginx supervisor

# 安装 geckodriver
wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
tar -xzf geckodriver-v0.36.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
```

#### 后端部署

```bash
cd gpt-researcher

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r multi_agents/requirements.txt

# 配置环境变量
export OPENAI_API_KEY=sk-your-key
export TAVILY_API_KEY=tvly-your-key

# 启动后端
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

#### 前端部署

```bash
cd frontend/nextjs

# 安装依赖
npm install --legacy-peer-deps

# 构建生产版本
npm run build

# 启动前端
npm run start -- -p 3001
```

#### 配置 Nginx

```nginx
# /etc/nginx/sites-available/gpt-researcher
server {
    listen 80;
    server_name your-domain.com;

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /outputs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /reports {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### 方案 D：本地 LLM 部署（Ollama）

实现完全离线运行，无需外部 LLM API。

#### 安装 Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama3:8b
ollama pull nomic-embed-text  # 用于嵌入
```

#### 配置环境变量

```bash
# .env 文件
OPENAI_API_KEY=ollama  # 任意值，因为使用本地模型
OPENAI_BASE_URL=http://localhost:11434/v1
LLM_PROVIDER=ollama
FAST_LLM=llama3:8b
SMART_LLM=llama3:8b
STRATEGIC_LLM=llama3:8b
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

#### Docker Compose 扩展

```yaml
# docker-compose.ollama.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  gpt-researcher:
    depends_on:
      - ollama
    environment:
      OPENAI_BASE_URL: http://ollama:11434/v1

volumes:
  ollama_data:
```

运行：

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d
```

---

## 环境配置详解

### 完整环境变量参考

```bash
# ===== 必需配置 =====
OPENAI_API_KEY=sk-xxx                    # OpenAI API 密钥
TAVILY_API_KEY=tvly-xxx                  # Tavily 搜索 API 密钥

# ===== LLM 配置 =====
LLM_PROVIDER=openai                      # openai, ollama, anthropic 等
FAST_LLM=gpt-4o-mini                     # 快速任务使用的模型
SMART_LLM=gpt-4o                         # 主要推理模型
STRATEGIC_LLM=o1-preview                 # 策略规划模型
OPENAI_BASE_URL=https://api.openai.com/v1  # API 基础 URL

# ===== 搜索配置 =====
RETRIEVER=tavily                         # tavily, duckduckgo, google 等
GOOGLE_API_KEY=xxx                       # Google 搜索 API（可选）
GOOGLE_CX_KEY=xxx                        # Google 自定义搜索引擎 ID

# ===== 爬虫配置 =====
SCRAPER=bs                               # bs, playwright, selenium 等
MAX_SCRAPER_WORKERS=15                   # 最大并发爬虫数
SCRAPER_RATE_LIMIT_DELAY=0.0             # 请求间隔（秒）

# ===== 嵌入配置 =====
EMBEDDING_PROVIDER=openai                # openai, ollama, cohere 等
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ===== 本地文档 =====
DOC_PATH=./my-docs                       # 本地文档路径

# ===== 输出配置 =====
OUTPUT_PATH=./outputs                    # 报告输出路径

# ===== 日志配置 =====
LOGGING_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR

# ===== 前端配置 =====
NEXT_PUBLIC_GPTR_API_URL=http://localhost:8000  # 后端 API 地址
```

### 配置文件优先级

```
1. 环境变量 (最高优先级)
2. .env 文件
3. config/config.json
4. 代码默认值 (最低优先级)
```

---

## API 密钥与成本规划

### 必需的 API 服务

| 服务 | 用途 | 费用估算 | 免费额度 |
|------|------|----------|----------|
| OpenAI API | LLM 推理 | ~$0.01-0.06/次研究 | 无 |
| Tavily API | 网络搜索 | ~$0.001/次搜索 | 1000次/月 |

### 可选的 API 服务

| 服务 | 用途 | 费用 |
|------|------|------|
| Google Gemini | 图像生成 | 按量计费 |
| LangSmith | 追踪调试 | 免费层可用 |
| Firecrawl | 高级爬虫 | $19/月起 |

### 成本优化策略

```
策略 1：使用本地 LLM
├── Ollama + Llama 3 8B
├── 无 API 费用
└── 需要 GPU 硬件投入

策略 2：使用低成本 API
├── DeepSeek API（价格低廉）
├── Groq（免费层）
└── Together.ai（竞争性定价）

策略 3：混合策略
├── 简单查询 → 本地 Llama 3
├── 复杂研究 → GPT-4
└── 平衡成本与质量
```

---

## 安全配置

### 网络安全

#### 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### Nginx HTTPS 配置

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com
```

```nginx
# /etc/nginx/sites-available/gpt-researcher
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ... 其他配置
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 访问控制

#### 基础认证

```nginx
# 生成密码文件
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Nginx 配置
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... 代理配置
}
```

#### IP 白名单

```nginx
location / {
    allow 192.168.1.0/24;   # 内网
    allow 10.0.0.0/8;       # VPN
    deny all;
    # ... 代理配置
}
```

### API 密钥安全

```bash
# 使用 Docker secrets（推荐）
echo "sk-your-key" | docker secret create openai_api_key -

# 或使用 .env 文件并限制权限
chmod 600 .env
chown root:root .env
```

---

## 监控与运维

### 日志管理

#### 日志位置

```
Docker 部署:
├── docker compose logs gpt-researcher      # 后端日志
├── docker compose logs gptr-nextjs         # 前端日志
└── ./logs/                                  # 应用日志目录

原生部署:
├── /var/log/nginx/access.log               # Nginx 访问日志
├── /var/log/nginx/error.log                # Nginx 错误日志
├── ./logs/research.log                     # 研究任务日志
└── supervisorctl tail -f backend           # 实时日志
```

#### 日志轮转配置

```bash
# /etc/logrotate.d/gpt-researcher
/home/app/gpt-researcher/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 app app
}
```

### 健康检查

```bash
# 创建健康检查脚本
cat > /usr/local/bin/check-gptr.sh << 'EOF'
#!/bin/bash

# 检查后端
if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is DOWN"
    # 可选：重启服务
    # docker compose restart gpt-researcher
    exit 1
fi

# 检查前端
if ! curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend is DOWN"
    exit 1
fi

echo "All services healthy"
exit 0
EOF

chmod +x /usr/local/bin/check-gptr.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/check-gptr.sh") | crontab -
```

### 监控集成

#### Prometheus + Grafana（可选）

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3030:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

### 备份策略

```bash
# 备份脚本
cat > /usr/local/bin/backup-gptr.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup/gpt-researcher
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份输出和文档
tar -czf $BACKUP_DIR/outputs_$DATE.tar.gz ./outputs
tar -czf $BACKUP_DIR/my-docs_$DATE.tar.gz ./my-docs

# 备份配置
cp .env $BACKUP_DIR/env_$DATE

# 保留最近 7 天的备份
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-gptr.sh

# 每日备份
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-gptr.sh") | crontab -
```

---

## 扩展与优化

### 性能优化

#### 1. 增加 Worker 数量

```bash
# .env 或 docker-compose.yml
WORKERS=4  # 根据 CPU 核心数调整
```

#### 2. 启用缓存

```python
# 在代码中添加 Redis 缓存（需要修改源码）
# 或使用 Nginx 缓存静态资源
```

```nginx
# Nginx 缓存配置
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

#### 3. 优化爬虫性能

```bash
# .env
MAX_SCRAPER_WORKERS=20          # 增加并发数
SCRAPER_RATE_LIMIT_DELAY=0.5    # 适当的请求间隔
```

### 水平扩展

#### 使用 Nginx 负载均衡

```nginx
upstream gpt_researcher_backend {
    server 127.0.0.1:8000 weight=1;
    server 127.0.0.1:8001 weight=1;
    server 127.0.0.1:8002 weight=1;
}

server {
    location /ws {
        proxy_pass http://gpt_researcher_backend;
        # ... WebSocket 配置
    }
}
```

#### 启动多个后端实例

```bash
# 启动多个后端 worker
uvicorn main:app --host 0.0.0.0 --port 8000 &
uvicorn main:app --host 0.0.0.0 --port 8001 &
uvicorn main:app --host 0.0.0.0 --port 8002 &
```

### 持久化知识库（进阶）

当前项目没有持久化知识库，可以添加：

```bash
# 添加向量数据库
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# 配置环境变量
VECTOR_STORE=qdrant
QDRANT_URL=http://localhost:6333
```

---

## 常见问题解决

### 问题 1：容器启动失败

```bash
# 检查日志
docker compose logs gpt-researcher

# 常见原因：
# 1. API 密钥未配置
# 2. 端口被占用
# 3. 权限问题

# 解决方案
docker compose down
docker compose up -d --build
```

### 问题 2：WebSocket 连接失败

```bash
# 检查 Nginx 配置
nginx -t

# 确保 WebSocket 头部正确
location /ws {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 问题 3：爬虫超时

```bash
# 增加超时时间
# 在 Nginx 配置中添加
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
```

### 问题 4：内存不足

```bash
# 限制容器内存
docker compose up -d --scale gpt-researcher=1 \
  --memory=4g --memory-swap=8g

# 或在 docker-compose.yml 中配置
services:
  gpt-researcher:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 问题 5：GPU 未被识别

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 安装 NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

---

## 部署检查清单

### 部署前

- [ ] 硬件满足最低要求
- [ ] Docker 和 Docker Compose 已安装
- [ ] API 密钥已准备（OpenAI, Tavily）
- [ ] 域名和 SSL 证书（生产环境）

### 部署中

- [ ] `.env` 文件配置正确
- [ ] 防火墙规则已配置
- [ ] 服务成功启动
- [ ] 日志无错误

### 部署后

- [ ] 前端可正常访问
- [ ] 研究功能测试通过
- [ ] WebSocket 连接正常
- [ ] 备份计划已配置
- [ ] 监控已设置

---

## 推荐的部署顺序

```
初学者/快速验证:
├── 1. 方案 A (Docker Compose)
├── 2. 配置必需的 API 密钥
└── 3. 验证功能

生产环境:
├── 1. 方案 A (Docker Compose)
├── 2. 添加 HTTPS (Let's Encrypt)
├── 3. 配置访问控制
├── 4. 设置监控和备份
└── 5. 性能调优

离线/隐私优先:
├── 1. 方案 D (本地 LLM)
├── 2. 使用 DuckDuckGo 替代 Tavily
├── 3. 完全内网部署
└── 4. 无外部 API 依赖
```

---

*文档版本: 1.0*
*最后更新: 2025年*
