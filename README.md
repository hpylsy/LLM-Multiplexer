# AI Relay Portal（AI 中转站门户）

一个开箱即用的 **大模型 API 中转站管理门户**，为团队提供统一的 API 密钥管理、使用量统计、成员额度管控和可视化仪表盘。

搭配 [CLIProxyAPIPlus](https://github.com/hpylsy/CLIProxyAPI) 使用，可以快速搭建一套完整的团队 AI API 中转 + 管理方案。

![首页截图](docs/screenshots/home.png)

---

## ✨ 功能特性

- 📊 **实时仪表盘** — 请求量、Token 消耗（输入/输出/缓存/思考）、费用、错误率
- 👥 **成员管理** — 按组/年级管理，支持批量启用/停用/删除
- 🔑 **密钥管理** — 绑定 CLIProxy 密钥，支持申请/审批流程
- 📈 **使用统计** — 按模型、按用户、按时间段查看，支持自定义日期范围
- 💰 **额度管控** — 月度 Token/费用额度配置与监控
- 🔄 **自动同步** — 从 CLIProxy 管理接口自动拉取使用记录（仅同步本队密钥）
- 🎨 **完全可定制** — 品牌名称、Logo、背景图、分组 emoji 均可配置
- 📱 **响应式设计** — 移动端友好，毛玻璃 UI 风格

---

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Django 4.2 + Gunicorn |
| 数据库 | PostgreSQL 16 |
| 前端 | Bootstrap 5.3 + Chart.js 4 |
| 部署 | Docker Compose 或 裸机 + Nginx |
| API 代理 | [CLIProxyAPIPlus](https://github.com/hpylsy/CLIProxyAPI) |

---

## 📋 前置要求

- 一台 Linux 服务器（推荐 2G 内存以上）
- Python 3.10+
- PostgreSQL 12+
- 一个运行中的 [CLIProxyAPIPlus](https://github.com/hpylsy/CLIProxyAPI)
- （可选）Docker + Docker Compose

---

## 🚀 快速开始

### 第一步：部署 CLIProxyAPIPlus（API 代理）

门户需要配合 API 代理使用。如果你还没有部署代理：

```bash
# 参考 CLIProxyAPIPlus 的文档部署
# https://github.com/hpylsy/CLIProxyAPI
```

部署完成后你会得到：
- **代理地址**（给用户用）：如 `http://your-server:8320/v1`
- **管理接口地址**（门户用来同步数据）：如 `http://127.0.0.1:8317`
- **管理密钥**：如 `YOUR_MANAGEMENT_KEY`

### 第二步：部署门户

#### 方式一：裸机部署（推荐新手）

```bash
# 1. 克隆仓库
git clone https://github.com/hpylsy/pioneer-portal.git
cd pioneer-portal

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 安装 PostgreSQL（如果还没有）
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser --createdb lab_portal
sudo -u postgres createdb -O lab_portal lab_portal

# 4. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置，见下方说明

# 5. 初始化数据库
python manage.py migrate

# 6. 创建管理员账号
python manage.py createsuperuser

# 7. 生成 Favicon（需要先放好 Logo）
pip install Pillow
python scripts/generate_favicon.py

# 8. 收集静态文件
python manage.py collectstatic --noinput

# 9. 启动服务
gunicorn lab_portal.wsgi:application --bind 127.0.0.1:8002 --workers 2 --timeout 120
```

#### 方式二：Docker Compose

```bash
# 1. 克隆仓库
git clone https://github.com/hpylsy/pioneer-portal.git
cd pioneer-portal

# 2. 配置
cp .env.example .env
nano .env  # 编辑配置

# 3. 启动
docker compose up -d

# 4. 创建管理员
docker compose exec web python manage.py createsuperuser

# 5. 访问 http://localhost:8080
```

### 第三步：配置 Nginx（裸机部署需要）

```nginx
server {
    listen 80;
    server_name your-server-ip;

    client_max_body_size 20m;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location /static/ {
        alias /path/to/pioneer-portal/staticfiles/;
        expires 7d;
    }

    location /media/ {
        alias /path/to/pioneer-portal/media/;
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

### 第四步：配置 systemd 开机自启（裸机部署）

```bash
sudo nano /etc/systemd/system/portal.service
```

```ini
[Unit]
Description=AI Relay Portal
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/pioneer-portal
ExecStart=/path/to/pioneer-portal/.venv/bin/gunicorn lab_portal.wsgi:application --bind 127.0.0.1:8002 --workers 2 --timeout 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable portal
sudo systemctl start portal
```

---

## ⚙️ 配置说明

编辑 `.env` 文件：

```env
# === 必须修改 ===
DJANGO_SECRET_KEY=用下面命令生成一个随机字符串
# python3 -c "import secrets; print(secrets.token_urlsafe(50))"

DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-server-ip
DJANGO_CSRF_TRUSTED_ORIGINS=http://your-server-ip

# === 数据库 ===
POSTGRES_DB=lab_portal
POSTGRES_USER=lab_portal
POSTGRES_PASSWORD=设置一个强密码
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# === CLIProxy 连接（关键！）===
CLIPROXY_BASE_URL=http://your-server-ip:8320
CLIPROXY_MANAGEMENT_BASE_URL=http://127.0.0.1:8317
CLIPROXY_MANAGEMENT_KEY=你的管理密钥

# === 品牌定制 ===
SITE_TITLE=你的团队AI中转站
SITE_SUBTITLE=Your Team AI Relay
SITE_DESCRIPTION=面向团队成员统一提供大模型中转服务。
SITE_TEAM_NAME=你的团队名
SITE_MOTTO=你的团队格言（留空则不显示）
SITE_MOTTO_DESCRIPTION=格言描述
```

---

## 🎨 品牌定制

### 替换 Logo 和背景

将你的图片放到 `static/brand/` 目录：

| 文件 | 用途 | 建议尺寸 |
|------|------|----------|
| `team-logo.png` | 导航栏 Logo + Favicon | 256×256 正方形 PNG |
| `background-main.jpg` | 首页背景 | 1920×1080 |
| `dashboard-background.jpg` | 仪表盘背景 | 1920×1080 |
| `team-motto.jpg` | 格言卡片背景 | 1200×400 |

替换后运行：
```bash
python scripts/generate_favicon.py  # 生成 favicon
python manage.py collectstatic --noinput
```

### 自定义分组 emoji

编辑 `core/templatetags/ui_tags.py` 中的 `GROUP_EMOJI` 字典：

```python
GROUP_EMOJI = {
    "你的组1": "⚡",
    "你的组2": "💻",
    "你的组3": "⚙️",
    "你的组4": "🎨",
}
```

---

## 📖 使用指南

### 管理员首次配置

1. **登录管理后台** → 用 createsuperuser 创建的账号登录
2. **创建用户** → 用户列表 → 创建用户并绑定 Key（需要 CLIProxy 分配的 API Key）
3. **同步数据** → 导入日志 → 点击"从 CLIProxy 同步"
4. **配置价格** → 模型价格 → 选择未定价模型并设置单价

### 普通用户

1. 登录后查看"公开面板"了解全队使用情况
2. "使用记录"查看个人 Token 类型分布和调用明细
3. "我的额度"查看 API 密钥、Base URL（点击即可复制）

---

## 🔧 运维命令

```bash
# 手动同步 CLIProxy 数据
python manage.py sync_cliproxy_usage

# 重建每日统计（如果数据异常）
python manage.py rebuild_daily_stats

# 数据完整性检查
python scripts/check_data.py
```

---

## 📁 项目结构

```
pioneer-portal/
├── lab_portal/          # Django 项目配置
├── core/                # 核心（首页、健康检查、权限装饰器）
├── users/               # 用户管理（Profile、批量操作）
├── api_keys/            # API 密钥管理
├── usage/               # 使用记录（同步、导入、聚合）
├── dashboard/           # 仪表盘（公开/管理面板、模型定价）
├── quota/               # 额度管理
├── templates/           # HTML 模板
├── static/
│   ├── brand/           # 品牌资源（替换这里的图片）
│   └── css/             # 样式表
├── scripts/             # 工具脚本
├── deployment/          # 部署配置参考
├── docker-compose.yml   # Docker 编排
└── .env.example         # 环境变量模板
```

---

## 🔗 相关项目

- **[CLIProxyAPIPlus](https://github.com/hpylsy/CLIProxyAPI)** — 本门户配套的 API 代理服务，支持多模型转发、用量统计、管理接口

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

## 📄 License

MIT License
