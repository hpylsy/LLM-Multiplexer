# AI Relay Portal（AI 中转站门户）

一个开箱即用的 **大模型 API 中转站管理门户**，为团队提供统一的 API 密钥管理、使用量统计、成员额度管控和可视化仪表盘。

![首页截图](docs/screenshots/home.png)

## ✨ 功能特性

- 📊 **实时仪表盘** — 请求量、Token 消耗、费用、错误率一目了然
- 👥 **成员管理** — 按组/年级管理成员，分配 API 密钥
- 🔑 **密钥管理** — 绑定 CLIProxy 密钥，支持申请/审批流程
- 📈 **使用统计** — 按模型、按用户、按时间段查看详细用量
- 💰 **额度管控** — 月度 Token/费用额度配置与监控
- 🔄 **自动同步** — 从 CLIProxy 管理接口自动拉取使用记录
- 🎨 **完全可定制** — 品牌名称、Logo、背景图均可通过配置替换
- 📱 **响应式设计** — 移动端友好，毛玻璃 UI 风格

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Django 4.2 + Gunicorn |
| 数据库 | PostgreSQL 16 |
| 前端 | Bootstrap 5.3 + Chart.js |
| 部署 | Docker Compose / 裸机 + Nginx |

## 📋 前置要求

- Python 3.10+
- PostgreSQL 12+
- 一个运行中的 [CLIProxy](https://github.com/musistudio/cli-proxy-api)（或兼容的 OpenAI API 代理）
- （可选）Docker + Docker Compose

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/ai-relay-portal.git
cd ai-relay-portal

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少修改以下项：
#   DJANGO_SECRET_KEY（生成随机字符串）
#   POSTGRES_PASSWORD
#   CLIPROXY_BASE_URL
#   CLIPROXY_MANAGEMENT_KEY
#   SITE_TITLE（你的站点名称）

# 3. 替换品牌资源（可选）
# 将你的 Logo 放到 static/brand/team-logo.png
# 将背景图放到 static/brand/background-main.jpg

# 4. 启动
docker compose up -d

# 5. 创建管理员
docker compose exec web python manage.py createsuperuser

# 6. 访问
# http://localhost:8080
```

### 方式二：裸机部署

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/ai-relay-portal.git
cd ai-relay-portal

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env（参考上方说明）
# 注意：裸机部署时 POSTGRES_HOST 改为 localhost

# 4. 初始化数据库
python manage.py migrate
python manage.py createsuperuser

# 5. 生成 Favicon
pip install Pillow
python scripts/generate_favicon.py

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 启动
gunicorn lab_portal.wsgi:application --bind 127.0.0.1:8002 --workers 2

# 8. 配置 Nginx 反向代理（见下方）
```

---

## ⚙️ 配置说明

### 环境变量一览

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DJANGO_SECRET_KEY` | Django 密钥（**必须修改**） | - |
| `DJANGO_DEBUG` | 调试模式 | `True` |
| `DJANGO_ALLOWED_HOSTS` | 允许的域名/IP | `127.0.0.1,localhost` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF 信任源 | `http://127.0.0.1` |
| `POSTGRES_DB` | 数据库名 | `lab_portal` |
| `POSTGRES_USER` | 数据库用户 | `lab_portal` |
| `POSTGRES_PASSWORD` | 数据库密码 | `lab_portal_password` |
| `POSTGRES_HOST` | 数据库地址 | `db`（Docker）/ `localhost` |
| `POSTGRES_PORT` | 数据库端口 | `5432` |
| `CLIPROXY_BASE_URL` | CLIProxy 对外地址（给用户用） | - |
| `CLIPROXY_MANAGEMENT_BASE_URL` | CLIProxy 管理接口地址 | - |
| `CLIPROXY_MANAGEMENT_KEY` | 管理接口认证密钥 | - |
| `SITE_TITLE` | 站点标题 | `AI中转站` |
| `SITE_SUBTITLE` | 站点副标题 | `AI Relay Console` |
| `SITE_DESCRIPTION` | 站点描述 | 面向团队成员... |
| `SITE_TEAM_NAME` | 团队名称 | - |
| `SITE_MOTTO` | 团队格言（留空则不显示） | - |
| `SITE_MOTTO_DESCRIPTION` | 格言描述 | - |

### 品牌定制

1. **替换 Logo**：将你的 Logo 放到 `static/brand/team-logo.png`（正方形 PNG）
2. **替换背景图**：替换 `static/brand/` 下的 jpg 文件
3. **修改站名**：在 `.env` 中设置 `SITE_TITLE`、`SITE_SUBTITLE`
4. **生成 Favicon**：运行 `python scripts/generate_favicon.py`
5. **收集静态文件**：运行 `python manage.py collectstatic --noinput`

详细说明见 [`static/brand/README.md`](static/brand/README.md)

---

## 🌐 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20m;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location /static/ {
        alias /path/to/ai-relay-portal/staticfiles/;
        expires 7d;
    }

    location /media/ {
        alias /path/to/ai-relay-portal/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📖 使用指南

### 管理员操作

1. **创建用户**：管理面板 → 用户列表 → 创建用户并绑定 Key
2. **同步数据**：管理面板 → 导入日志 → 点击"CLIProxy 同步"
3. **配置价格**：管理面板 → 模型价格 → 添加模型定价

### 普通用户

1. 登录后查看"公开面板"了解全队使用情况
2. "使用记录"查看个人详细调用日志
3. "我的额度"查看 API 密钥和 Base URL

---

## 🔧 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python manage.py runserver

# 重建每日统计
python manage.py rebuild_daily_stats

# 手动同步 CLIProxy
python manage.py sync_cliproxy_usage
```

---

## 📁 项目结构

```
ai-relay-portal/
├── lab_portal/          # Django 项目配置
├── core/                # 核心功能（首页、健康检查、工具函数）
├── users/               # 用户管理（Profile、管理员操作）
├── api_keys/            # API 密钥管理
├── usage/               # 使用记录（同步、导入、聚合）
├── dashboard/           # 仪表盘（公开/管理面板）
├── quota/               # 额度管理
├── templates/           # HTML 模板
├── static/              # 静态资源
│   ├── brand/           # 品牌资源（Logo、背景图）
│   └── css/             # 样式表
├── scripts/             # 部署和工具脚本
├── deployment/          # 部署配置（Nginx）
├── docker-compose.yml   # Docker 编排
├── Dockerfile           # 容器构建
└── .env.example         # 环境变量模板
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

## 📄 License

MIT License
