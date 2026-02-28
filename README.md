# FaultSeeker — Deployment Guide / 部署指南

> **English** | [中文](#中文部署指南)

---

## English Deployment Guide

### Overview

FaultSeeker consists of two services:

| Service  | Technology | Default Port |
|----------|-----------|--------------|
| Backend  | Python / FastAPI | 8000 |
| Frontend | Vue 3 / Vite (or Nginx in production) | 5173 (dev) / 80 (prod) |

The backend depends on the `faultseeker` core library (included in this folder) and requires an **OpenRouter API key** to call the AI analysis pipeline.

---

### Prerequisites

**Option A — Docker (recommended for production)**
- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2
- Foundry is installed automatically inside the container.

**Option B — Local (development)**
- Python ≥ 3.10
- Node.js ≥ 18
- [Foundry](https://book.getfoundry.sh/getting-started/installation) — the `cast` binary is required for transaction replay:
  ```bash
  curl -L https://foundry.paradigm.xyz | bash
  foundryup
  ```

---

### Step 1 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> Get a key at https://openrouter.ai
> **Never commit `.env` to version control.**

---

### Step 2A — Deploy with Docker (Production)

```bash
docker compose up --build -d
```

The application will be available at **http://localhost** (port 80).

To view logs:

```bash
docker compose logs -f
```

To stop:

```bash
docker compose down
```

---

### Step 2B — Run Locally (Development)

Use the provided script to start both servers with one command:

```bash
bash start-dev.sh
```

Or start them manually:

```bash
# Terminal 1 — Backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt -r backend/requirements.txt
venv/bin/pip install -e .
venv/bin/uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | API key from openrouter.ai |
| `FAULTSEEKER_MODEL` | No | `openai/gpt-4o-mini` | Model to use for analysis |

### RPC Endpoints (foundry.toml)

`foundry.toml` configures the RPC endpoints used by `cast run` during transaction replay. The included file uses free public endpoints. For better reliability in production, replace the URLs with paid endpoints (e.g. Alchemy or Infura):

```toml
rpc_endpoints = {
  eth  = "https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
  bsc  = "https://bnb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
  ...
}
```

---

### Project Structure

```
deploy/
├── backend/            # FastAPI backend (SSE + rate limiter)
├── frontend/           # Vue 3 frontend source
├── faultseeker/        # Core analysis library
├── setup.py            # Python package setup
├── requirements.txt    # Core library dependencies
├── .env.example        # Environment variable template
├── Dockerfile.backend  # Backend container image
├── Dockerfile.frontend # Frontend container image (multi-stage build)
├── docker-compose.yml  # Service orchestration
├── nginx.conf          # Nginx reverse proxy config
└── start-dev.sh        # One-command dev launcher
```

---

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `OPENROUTER_API_KEY` not found | Ensure `.env` exists and the key is set correctly |
| Port 80 already in use | Edit `docker-compose.yml` → change `"80:80"` to e.g. `"8080:80"` |
| SSE stream cuts off | Check `proxy_read_timeout` in `nginx.conf` (default: 600 s) |
| Backend fails to start | Run `docker compose logs backend` to inspect errors |

---

---

<a name="中文部署指南"></a>

## 中文部署指南

### 概览

FaultSeeker 由两个服务组成：

| 服务 | 技术栈 | 默认端口 |
|------|--------|---------|
| 后端 | Python / FastAPI | 8000 |
| 前端 | Vue 3 / Vite（生产环境由 Nginx 托管） | 5173（开发）/ 80（生产） |

后端依赖 `faultseeker` 核心库（已包含在本文件夹中），并需要 **OpenRouter API Key** 才能调用 AI 分析流程。

---

### 前置要求

**方案 A — Docker（推荐用于生产环境）**
- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2
- Foundry 会在容器内自动安装，无需手动操作。

**方案 B — 本地运行（开发环境）**
- Python ≥ 3.10
- Node.js ≥ 18
- [Foundry](https://book.getfoundry.sh/getting-started/installation) — 交易回放依赖 `cast` 命令：
  ```bash
  curl -L https://foundry.paradigm.xyz | bash
  foundryup
  ```

---

### 第一步 — 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
OPENROUTER_API_KEY=你的_openrouter_api_key
```

> 在 https://openrouter.ai 获取 API Key
> **切勿将 `.env` 提交到版本控制系统。**

---

### 第二步 A — Docker 部署（生产环境）

```bash
docker compose up --build -d
```

部署完成后，访问 **http://localhost**（80 端口）即可使用。

查看日志：

```bash
docker compose logs -f
```

停止服务：

```bash
docker compose down
```

---

### 第二步 B — 本地运行（开发环境）

使用内置脚本一键启动前后端：

```bash
bash start-dev.sh
```

或手动分别启动：

```bash
# 终端 1 — 后端
python3 -m venv venv
venv/bin/pip install -r requirements.txt -r backend/requirements.txt
venv/bin/pip install -e .
venv/bin/uvicorn backend.main:app --reload --port 8000

# 终端 2 — 前端
cd frontend
npm install
npm run dev
```

在浏览器中打开 **http://localhost:5173**。

---

### 环境变量说明

| 变量名 | 是否必填 | 默认值 | 说明 |
|--------|---------|--------|------|
| `OPENROUTER_API_KEY` | 是 | — | openrouter.ai 的 API Key |
| `FAULTSEEKER_MODEL` | 否 | `openai/gpt-4o-mini` | 分析使用的模型 |

### RPC 端点配置（foundry.toml）

`foundry.toml` 配置了 `cast run` 执行交易回放时所用的 RPC 端点。默认使用免费公共节点，生产环境建议替换为付费节点（如 Alchemy、Infura）以获得更高稳定性：

```toml
rpc_endpoints = {
  eth  = "https://eth-mainnet.g.alchemy.com/v2/你的_ALCHEMY_KEY",
  bsc  = "https://bnb-mainnet.g.alchemy.com/v2/你的_ALCHEMY_KEY",
  ...
}
```

---

### 目录结构

```
deploy/
├── backend/            # FastAPI 后端（SSE + 限流器）
├── frontend/           # Vue 3 前端源码
├── faultseeker/        # 核心分析库
├── setup.py            # Python 包配置
├── requirements.txt    # 核心库依赖
├── .env.example        # 环境变量模板
├── Dockerfile.backend  # 后端容器镜像
├── Dockerfile.frontend # 前端容器镜像（多阶段构建）
├── docker-compose.yml  # 服务编排配置
├── nginx.conf          # Nginx 反向代理配置
└── start-dev.sh        # 开发环境一键启动脚本
```

---

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| 提示找不到 `OPENROUTER_API_KEY` | 确认 `.env` 文件存在且 Key 填写正确 |
| 80 端口被占用 | 修改 `docker-compose.yml`，将 `"80:80"` 改为如 `"8080:80"` |
| SSE 流中断 | 检查 `nginx.conf` 中的 `proxy_read_timeout`（默认 600 秒） |
| 后端启动失败 | 执行 `docker compose logs backend` 查看详细错误信息 |
