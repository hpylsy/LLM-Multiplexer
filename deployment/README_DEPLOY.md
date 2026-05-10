# 部署补充说明

## 初始化顺序

1. 复制 [` .env.example`](../.env.example) 为 `.env`
2. 执行 `docker compose up -d --build`
3. 执行 `docker compose exec web python manage.py createsuperuser`
4. 登录 Django Admin 或前台管理员页面

## 生产环境建议

- 设置 `DJANGO_DEBUG=False`
- 将 `DJANGO_ALLOWED_HOSTS` 改成实际域名/IP
- 配置 HTTPS 反代
- 定期备份 PostgreSQL 数据卷
