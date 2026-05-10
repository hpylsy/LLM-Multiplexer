# Pioneer Portal 部署与迁移说明

本文档专门用于说明如何把 [`pioneer-portal`](../pioneer-portal/README.md) 迁移到远端服务器，并说明：

- 迁移后哪些配置必须修改
- 如何与远端已有的 [`cli-proxy-api`](../cliproxyapi/cli-proxy-api) 协同工作
- 什么情况下需要修改远端 CLIProxy
- 上线后的推荐部署方式与排障方法

---

## 1. 先说结论

### 1.1 [`pioneer-portal`](../pioneer-portal/README.md) 一定要改什么

迁移到远端后，至少需要修改这些内容：

1. Django 环境变量
2. 数据库连接信息
3. 允许访问的域名 / IP
4. 供门户拉取 usage 的 CLIProxy 管理接口地址
5. 静态文件与运行方式（开发模式不能直接当生产模式长期跑）

### 1.2 远端的 [`cli-proxy-api`](../cliproxyapi/cli-proxy-api) 要不要改

**分情况：**

- 如果远端 CLIProxy **已经稳定运行**，并且你只想让门户读取它的 usage / 管理接口，**通常不用改 CLIProxy 主程序本体**。
- 你只需要确认：
  - CLIProxy 正在运行
  - 管理接口可访问
  - 返回的数据格式和门户当前读取逻辑兼容
- 只有在以下情况才需要改远端 CLIProxy：
  1. 管理接口端口不对
  2. 管理接口路径不是门户当前使用的路径
  3. 远端没开启管理接口
  4. usage 返回格式和门户解析逻辑不一致

也就是说，**优先改门户配置，不要先动远端 CLIProxy 代码**。

---

## 2. 迁移前，你应该准备什么

建议远端至少具备：

- Linux 服务器
- Python 3.10+ 或 3.11
- PostgreSQL
- Nginx（推荐）
- systemd（推荐）

你计划把 [`pioneer-portal`](../pioneer-portal/README.md) 推到 GitHub，再拉到远端，这个流程是对的。

建议远端目录类似：

```text
/home/youruser/
├── pioneer-portal/
├── cli-proxy/
│   ├── cli-proxy-api
│   └── config.yaml
└── venvs/
    └── pioneer-portal-venv/
```

其中：

- [`pioneer-portal`](../pioneer-portal/README.md) 放新门户代码
- [`cli-proxy-api`](../cliproxyapi/cli-proxy-api) 继续作为远端代理主程序
- Python 虚拟环境建议**单独放**，不要再放旧目录里，避免以后误删

---

## 3. 迁移到远端的标准步骤

## 3.1 拉取代码

在远端服务器执行：

```bash
git clone <你的 GitHub 仓库地址> pioneer-portal
cd pioneer-portal
```

## 3.2 创建虚拟环境并安装依赖

```bash
python3 -m venv /home/youruser/venvs/pioneer-portal-venv
source /home/youruser/venvs/pioneer-portal-venv/bin/activate
pip install -r requirements.txt
```

## 3.3 准备环境变量

如果仓库中有 [`.env.example`](../pioneer-portal/.env.example)，先复制：

```bash
cp .env.example .env
```

然后重点修改以下配置。

---

## 4. 迁移后 [`pioneer-portal`](../pioneer-portal/README.md) 必须改的配置

## 4.1 Django 基础配置

至少保证这些变量正确：

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

例如：

```env
DJANGO_SECRET_KEY=换成你自己的强随机字符串
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,server-ip,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,http://server-ip
```

如果这些不改，常见问题包括：

- 无法通过域名访问
- CSRF 403
- Debug 页面暴露

---

## 4.2 数据库配置

你需要让远端门户连接自己的 PostgreSQL，而不是本地开发数据库。

确保：

- 数据库已创建
- 用户有权限
- `.env` 中数据库主机、端口、库名、用户名、密码正确

迁移后执行：

```bash
python manage.py migrate
python manage.py createsuperuser
```

如果你已经有数据迁移方案，也可以导入旧数据后再启动。

---

## 4.3 最关键配置：CLIProxy 管理接口地址

从你现在的报错看，门户会去请求：

- `http://127.0.0.1:8317/v0/management/usage`

这说明 [`fetch_cliproxy_usage_records()`](usage/services.py:112) 依赖一个 **CLIProxy 管理接口地址**。

所以迁移后必须确认两件事：

1. 远端 CLIProxy 的管理接口是不是也监听在 `127.0.0.1:8317`
2. 路径是不是 `/v0/management/usage`

### 推荐部署关系

如果 CLIProxy 和门户在**同一台服务器**：

- CLIProxy 管理接口建议继续只监听本机，例如：`127.0.0.1:8317`
- 门户服务本机访问它即可

如果 CLIProxy 和门户在**不同服务器**：

- 需要把门户配置改成 CLIProxy 所在服务器地址
- 同时做好防火墙 / 反向代理 / 白名单控制

### 推荐原则

优先改门户读取地址，不优先改 CLIProxy 程序。

---

## 5. 怎么判断远端 CLIProxy 要不要改

## 5.1 不需要改的情况

如果远端 CLIProxy 满足以下条件，就**不需要修改 CLIProxy**：

1. 代理功能正常
2. 管理接口可用
3. 访问下面地址有返回：

```bash
curl http://127.0.0.1:8317/v0/management/usage
```

4. 返回数据字段能被 [`usage/services.py`](usage/services.py) 正常解析

这种情况下，你只需要让 [`pioneer-portal`](../pioneer-portal/README.md) 对准这个地址即可。

## 5.2 需要改的情况

只有这些情况才建议改远端 CLIProxy：

### 情况 A：管理接口根本没开

表现：

- 门户一直报连接拒绝
- `curl` 管理接口失败

这时要检查远端 CLIProxy 的配置文件 [`config.yaml`](../cliproxyapi/config.yaml) 是否开启管理接口。

### 情况 B：端口不是 `8317`

如果远端实际监听的是其他端口，比如 `9000`，那就：

- 要么改门户配置
- 要么改 CLIProxy 配置统一端口

**优先建议改门户配置。**

### 情况 C：路径不一致

如果远端提供的是别的路径，而不是：

- `/v0/management/usage`

那就需要：

- 修改门户的对接地址
- 或修改 CLIProxy 的管理路由

仍然建议**优先改门户**。

### 情况 D：返回 JSON 结构不同

如果远端 CLIProxy 版本和你现在本地用来适配的版本不同，返回字段可能不一样。

这时通常要调整的是门户里的解析逻辑：

- [`normalize_usage_record()`](usage/services.py:31)
- [`resolve_related_objects()`](usage/services.py:63)
- [`fetch_cliproxy_usage_records()`](usage/services.py:105)

而不是先去动 CLIProxy 主体。

---

## 6. 推荐你在远端做的验证顺序

## 6.1 先验证 CLIProxy 本身

先在远端确认代理服务活着：

```bash
ps -ef | grep cli-proxy-api
ss -ltnp | grep 8317
```

然后验证管理接口：

```bash
curl http://127.0.0.1:8317/v0/management/usage
```

### 如果返回正常

说明 CLIProxy 基本不用动。

### 如果连接拒绝

说明：

- 要么 CLIProxy 没启动
- 要么管理接口没开
- 要么端口不对

这个时候才去看远端的 [`config.yaml`](../cliproxyapi/config.yaml)。

---

## 6.2 再验证门户数据库

```bash
python manage.py migrate
python manage.py check
python manage.py createsuperuser
```

如果 [`python manage.py check`](manage.py:1) 能过，说明 Django 项目基础没问题。

---

## 6.3 再验证门户能否拉到 usage

登录门户后，观察：

- 首页
- [`/dashboard/public/`](templates/dashboard/public_dashboard.html)
- [`/dashboard/admin/`](templates/dashboard/admin_dashboard.html)
- [`/usage/sync/status/`](usage/views.py:53)

如果这里报错，优先看：

- CLIProxy 管理接口连通性
- 门户环境变量中的管理接口地址

---

## 7. 生产环境推荐部署方式

不要长期直接使用：

```bash
python manage.py runserver 0.0.0.0:8002
```

推荐使用：

- Gunicorn + systemd
- Nginx 反向代理

## 7.1 Gunicorn 示例

```bash
gunicorn lab_portal.wsgi:application --bind 127.0.0.1:8002
```

## 7.2 Nginx 反代示例思路

Nginx 对外监听 80/443，然后反向代理到：

- `127.0.0.1:8002`

静态文件由 Nginx 直接托管。

---

## 8. 是否要把远端 CLIProxy 和门户放在一起

推荐：**可以在同机部署，但分目录管理。**

例如：

- CLIProxy：`/opt/cliproxy/`
- Portal：`/opt/pioneer-portal/`

这样好处是：

1. 门户升级不影响 CLIProxy 主程序
2. CLIProxy 升级也不影响门户代码
3. 出问题时更容易排查

---

## 9. 你迁移后大概率需要手工改的地方清单

下面是一份真正落地时的 checklist：

### 门户侧必须检查

- [ ] GitHub 代码已拉到远端
- [ ] Python 虚拟环境已建立
- [ ] 依赖已安装
- [ ] `.env` 已配置
- [ ] PostgreSQL 已准备好
- [ ] 执行过 [`python manage.py migrate`](manage.py:1)
- [ ] 执行过 [`python manage.py check`](manage.py:1)
- [ ] 已创建管理员账号
- [ ] 静态文件已处理
- [ ] Gunicorn / systemd / Nginx 已配置

### CLIProxy 侧必须检查

- [ ] [`cli-proxy-api`](../cliproxyapi/cli-proxy-api) 正在远端运行
- [ ] [`config.yaml`](../cliproxyapi/config.yaml) 配置正确
- [ ] 管理接口可以从门户所在机器访问
- [ ] `/v0/management/usage` 返回正常

---

## 10. 关于“远端 cliproxy 是否需要修改”的最终建议

最终建议非常明确：

### 优先级 1：先不改远端 CLIProxy 代码

先做这些：

1. 启动远端 CLIProxy
2. 确认管理接口地址
3. 修改门户配置去对接它

### 优先级 2：只有接口不兼容时，才改门户解析逻辑

优先改：

- [`usage/services.py`](usage/services.py)

因为这属于适配层，风险更小。

### 优先级 3：最后才考虑改 CLIProxy 本体

只有当远端版本过老、根本不提供当前所需管理能力时，再考虑升级或修改 CLIProxy。

---

## 11. 迁移完成后的首轮自测命令

你把代码传上远端后，建议按下面顺序测试：

```bash
cd /path/to/pioneer-portal
source /path/to/venv/bin/activate
python manage.py check
python manage.py migrate
curl http://127.0.0.1:8317/v0/management/usage
python manage.py runserver 0.0.0.0:8002
```

然后浏览器验证：

- `/`
- `/accounts/login/`
- `/dashboard/public/`
- `/dashboard/admin/`
- `/usage/sync/status/`

---

## 12. 你现在这套项目在远端最可能遇到的坑

结合你当前本地现象，远端最容易出现的是：

### 坑 1：CLIProxy 管理接口没开

表现：

- [`/usage/sync/status/`](usage/views.py:53) 报 500
- 日志里出现 `Connection refused`

### 坑 2：门户能启动，但拉不到 usage

表现：

- 页面能打开
- 仪表盘没数据或自动同步报错

### 坑 3：域名能打开，但表单提交 403

表现：

- 登录页可开
- 登录 / POST 操作失败

一般是：

- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

没配好。

### 坑 4：静态文件丢失

表现：

- 页面有 HTML，但没样式
- 图片不显示

这通常是 Nginx 静态文件或 Django static 配置没处理好。

---

## 13. 推荐的最终部署思路

最推荐你采用下面的架构：

1. 远端保留已有 [`cli-proxy-api`](../cliproxyapi/cli-proxy-api)
2. 新建独立目录部署 [`pioneer-portal`](../pioneer-portal/README.md)
3. 门户通过本机地址读取 CLIProxy 管理接口
4. 不改 CLIProxy 主逻辑，优先改门户适配配置
5. 用 Gunicorn + Nginx 托管门户

这套方式风险最低，也最容易持续维护。

---

## 14. 一句话结论

把 [`pioneer-portal`](../pioneer-portal/README.md) 移植到远端后，**重点修改的是门户的环境变量、数据库配置和 CLIProxy 管理接口地址；远端 [`cli-proxy-api`](../cliproxyapi/cli-proxy-api) 通常不需要改代码，只需要确认它的管理接口确实可用。**
