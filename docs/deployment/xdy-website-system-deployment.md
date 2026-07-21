# 熊大爷官网系统架构与 Docker 部署运维文档

> 文档版本：1.0  
> 编制日期：2026-07-21  
> 适用站点：`xdy.secondlife.today` 及后续正式官网域名  
> 现网系统：OpenCloudOS 9.4，x86_64  
> 推荐目标系统：OpenCloudOS 9.4 或 Ubuntu Server 24.04 LTS，x86_64  
> 目标：将熊大爷官网前台、内容后台、反向代理和证书服务容器化，所有持久化目录统一放在 `/opt/docker-files/`，Docker 与 containerd 数据统一放在 `/opt/docker/`。

---

## 1. 文档结论

熊大爷官网目前不是传统的“前端 + API + 数据库”动态网站，而是一个**静态官网 + 轻量内容发布后台**：

1. 前台由 HTML、CSS、JavaScript、PWA 文件组成，浏览访问不依赖数据库和后端 API；
2. 内容后台使用 Python Flask + Waitress；
3. 后台以 `content.json` 保存结构化内容，通过 Jinja 模板重新生成静态 HTML；
4. 图片、视频主要存储在腾讯云 COS/CDN，官网服务器不承担大媒体文件分发；
5. 加盟表单数据使用 `leads.json` 保存；
6. 当前系统没有使用 MySQL、PostgreSQL、Redis、SQLite；
7. 当前线上入口由 Caddy 提供静态文件服务，并反向代理 `/admin/*` 与 `/api/*`。

按本文件迁移后，建议采用以下容器：

- `xdy-nginx`：公网入口、HTTPS、静态文件、后台反向代理；
- `xdy-admin`：Flask + Waitress 内容管理后台；
- `xdy-certbot`：Let's Encrypt 证书申请与续期；
- 可选监控：`node-exporter`、`cadvisor`；
- 二期可选：PostgreSQL，仅在多人协作、审核流、内容版本查询等需求明确后引入。

**基础生产环境不建议为了“看起来完整”而额外引入数据库、Redis、消息队列。** 当前文件型内容源符合系统规模，依赖少、恢复快、迁移成本低。

---

## 2. 当前系统盘点

### 2.1 前台系统

| 项目 | 当前实现 | 说明 |
|---|---|---|
| 页面形态 | 纯静态 HTML/CSS/JavaScript | 前台访问不调用业务 API |
| Web 目录 | 仓库根目录及 `web/`、`ds/`、`manual/`、`miniapp/` 等 | 官网、设计体系、品牌手册、小程序预览等共站部署 |
| PWA | `manifest.webmanifest`、`sw.js`、`pwa/` | HTML/CSS 网络优先，失败时使用缓存 |
| 图片/视频 | 腾讯云 COS/CDN | HTML 中主要使用 COS 绝对地址 |
| 本地静态体积 | 约 127 MB | 大部分媒体已外置，服务器磁盘压力较小 |

### 2.2 内容管理后台

| 项目 | 当前实现 | 说明 |
|---|---|---|
| 运行时 | Python 3.11.6 | 现网虚拟环境 `/srv/xdy-admin/.venv` |
| 框架 | Flask 3.1.3 | 运营后台和发布接口 |
| WSGI 服务 | Waitress 3.0.2 | 现网监听 `127.0.0.1:8787` |
| 模板引擎 | Jinja2 3.1.6 | 与后台运行时一起锁定版本 |
| COS SDK | cos-python-sdk-v5 1.9.44 | 后台媒体上传 |
| 内容源 | `content.json` | 当前官网结构化内容主数据 |
| 加盟留资 | `leads.json` | 包含潜在客户信息，按敏感业务数据保护 |
| 页面模板 | Jinja `templates/web.html.j2` | 将内容渲染为静态页面 |
| 发布结果 | 官网静态目录中的 `web/index.html` | 发布完成后前台仍是纯静态 |
| 登录 | 单账号 + 密码哈希 + Flask Session | 配置及密钥不可进入 Git |
| 图片上传 | 腾讯云 COS | 后台上传后回填 CDN URL |
| 发布备份 | 发布前备份旧 HTML，保留最近约 30 份 | 迁移后继续保留并增加整站备份 |

### 2.3 当前线上依赖

| 组件 | 当前状态 | Docker 化建议 |
|---|---|---|
| Caddy | 静态服务、HTTPS，代理 `/admin/*` 与 `/api/*` | 迁移为 Nginx + Certbot，便于企业运维标准化 |
| Flask | 内容后台 | 独立容器 |
| Waitress | Flask WSGI Server | 与后台打入同一应用镜像 |
| Jinja | 静态页模板渲染 | 与后台打入同一应用镜像 |
| 腾讯云 COS | 媒体存储/CDN | 保持外部托管，不在本机部署 MinIO |
| Git | 官网源代码与版本管理 | 部署机只读拉取或由 CI 发布 |
| 数据库 | 未使用 | 基础方案不部署 |
| Redis | 未使用 | 基础方案不部署 |

---

## 3. 目标架构

### 3.1 访问拓扑

```text
浏览器
  │ HTTPS 443
  ▼
[xdy-nginx]
  ├── /admin/*、/api/* ───────► [xdy-admin:8787]
  ├── /.well-known/acme-* ────► Certbot Webroot
  └── 其他路径 ───────────────► /srv/xdy-web/current 静态文件
                                      │
                                      ├── 官网 HTML/CSS/JS/PWA
                                      └── HTML 中引用腾讯云 COS/CDN 媒体

[xdy-admin]
  ├── 读取/写入 content.json 与 leads.json
  ├── 使用 Jinja 模板生成 HTML
  ├── 写入 /srv/xdy-web/current/web/index.html
  ├── 发布前写入 backups/
  └── 调用腾讯云 COS 上传接口
```

### 3.2 网络原则

- 仅 Nginx 暴露 `80` 和 `443`；
- 后台容器只加入 Docker 内部网络，不向宿主机直接开放 `8787`；
- Certbot 不开放端口；
- 后台管理入口必须只走 HTTPS；
- 可进一步通过企业 VPN、固定办公公网 IP 或 Zero Trust 限制 `/admin/`。

### 3.3 数据边界

| 数据 | 持久化位置 | 是否可重建 |
|---|---|---|
| Docker 镜像、层、容器元数据 | `/opt/docker/` | 可从镜像仓库/构建文件重建 |
| 官网发布文件 | `/opt/docker-files/xdy/web/` | 可从 Git + 内容后台重建 |
| `content.json` | `/opt/docker-files/xdy/admin/data/` | **不可丢失，官网内容主数据** |
| `leads.json` | `/opt/docker-files/xdy/admin/data/` | **不可丢失，加盟留资敏感数据** |
| 后台账户配置/密钥 | `/opt/docker-files/xdy/admin/secrets/` | **不可丢失，必须加密备份** |
| 发布备份 | `/opt/docker-files/xdy/admin/backups/` | 用于快速回滚 |
| Nginx 配置和日志 | `/opt/docker-files/xdy/nginx/` | 配置需备份，日志可按周期清理 |
| TLS 证书 | `/opt/docker-files/xdy/letsencrypt/` | 可重新签发，但应备份 |
| 腾讯云 COS 媒体 | 腾讯云 | 应开启版本控制/生命周期策略 |

---

## 4. 服务器目录规范

### 4.1 Docker 根目录

```text
/opt/docker/
├── engine/          # Docker Engine data-root
└── containerd/      # containerd 持久数据
```

说明：较新的 Docker Engine 安装可能使用 containerd image store。只修改 Docker `data-root` 不一定会移动 `/var/lib/containerd`，因此需要同时配置 containerd 根目录，才能满足 Docker 持久数据全部位于 `/opt/docker/` 的要求。

### 4.2 所有容器持久化目录

```text
/opt/docker-files/xdy/
├── compose/
│   ├── compose.yml
│   ├── .env
│   ├── Dockerfile.admin
│   └── requirements.txt
├── nginx/
│   ├── conf.d/
│   │   └── xdy.conf
│   └── logs/
├── web/
│   ├── releases/
│   │   └── <git-sha-or-timestamp>/
│   └── current -> releases/<active-release>
├── admin/
│   ├── app/                 # 后台源代码构建上下文；不直接映射到公网
│   ├── data/
│   │   ├── content.json
│   │   └── leads.json
│   ├── secrets/
│   │   ├── config.json
│   │   ├── flask-secret
│   │   └── cos.env
│   ├── backups/
│   └── logs/
├── certbot/
│   └── www/
├── letsencrypt/
│   ├── etc/
│   └── lib/
├── backup/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    ├── restore.sh
    └── health-check.sh
```

### 4.3 权限建议

- `/opt/docker/`：`root:root`，权限 `0711` 或更严格；
- Compose 和 Nginx 配置：`root:root`，目录 `0750`，文件 `0640`；
- 密钥目录：`root:root`，目录 `0700`，文件 `0600`；
- 后台数据、备份：由固定非 root UID/GID（示例 `10001:10001`）读写；
- Nginx 日志：Nginx 容器可写，宿主机运维组可读；
- 不对 `/opt/docker-files/xdy/admin/` 开启 Web 目录映射。

---

## 5. 服务器建议配置

### 5.1 单容器资源建议

| 服务 | CPU 最低/限制 | 内存最低/限制 | 磁盘 | 说明 |
|---|---:|---:|---:|---|
| Nginx | 0.10 / 0.50 核 | 64 / 256 MB | 日志 2–5 GB | 静态页开销很低 |
| Flask + Waitress | 0.25 / 1.00 核 | 256 / 768 MB | 数据及备份 5–10 GB | 发布时会短时增加 CPU/内存 |
| Certbot | 0.05 / 0.25 核 | 64 / 256 MB | 证书小于 1 GB | 仅续期时运行 |
| Docker Engine/containerd | — | 300–800 MB | 镜像及日志 10–20 GB | 宿主机开销 |
| 监控（可选） | 0.10 / 0.50 核 | 128 / 512 MB | 时序数据另算 | node-exporter/cAdvisor |
| PostgreSQL（二期可选） | 0.50 / 2.00 核 | 512 MB / 2 GB | 20 GB 起 | 当前基础系统不部署 |

### 5.2 服务器规格建议

#### 最低可运行

- 2 vCPU；
- 4 GB RAM；
- 60 GB SSD；
- 2 GB Swap；
- 5 Mbps 公网带宽；
- 适合内部预览、低频更新和较低访问量。

#### 推荐生产配置

- **4 vCPU；**
- **8 GB RAM；**
- **100 GB SSD；**
- **2–4 GB Swap；**
- **10 Mbps 或以上公网带宽；**
- 每日异机备份；
- 腾讯云 COS/CDN 承担图片和视频流量。

#### 未来多人 CMS / 数据库版本

- 4–8 vCPU；
- 8–16 GB RAM；
- 150 GB 以上 SSD；
- PostgreSQL 独立容器或云数据库；
- 数据库每日全量 + WAL/日志增量备份；
- 如后台并发、任务队列明确增加，再评估 Redis。

### 5.3 资源推导

当前前台为静态资源，且大图片/视频主要走 COS/CDN，实际服务器主要承担：

1. HTML/CSS/JS 小文件传输；
2. TLS 和 Nginx 连接；
3. 少量后台管理请求；
4. 内容发布时的一次模板渲染和文件写入。

因此瓶颈通常不是 CPU，而是：

- 配置或发布错误；
- 证书过期；
- `content.json`、`leads.json` 和密钥未备份；
- 容器日志无限增长；
- COS 凭据失效；
- DNS/CDN 配置异常。

推荐 4 核 8 GB 是为了给系统升级、日志、备份压缩、临时排障和未来后台扩展留出余量，而不是当前页面渲染本身需要该资源。

---

## 6. 安装 Docker 与 Compose

现网为 OpenCloudOS 9.4。以下先给出 OpenCloudOS 9.4 的安装方式，再给出 Ubuntu 24.04 LTS 备选方式。两种系统最终使用相同的目录、Docker daemon 和 Compose 配置。

### 6.1 基础初始化

先完成 6.2A 或 6.2B 的系统软件安装，再建立统一目录：

```bash
sudo -i

mkdir -p /opt/docker/engine /opt/docker/containerd
mkdir -p /opt/docker-files/xdy/{compose,nginx/conf.d,nginx/logs,web/releases,admin/app,admin/data,admin/secrets,admin/backups,admin/logs,certbot/www,letsencrypt/etc,letsencrypt/lib,backup/daily,backup/weekly,backup/monthly,scripts}
chmod 700 /opt/docker-files/xdy/admin/secrets
chown -R 10001:10001 /opt/docker-files/xdy/admin/{data,backups,logs}
chmod 750 /opt/docker-files/xdy/admin/{data,backups,logs}
```

### 6.2A OpenCloudOS 9.4 安装 Docker（现网推荐）

OpenCloudOS 9.4 使用 `dnf`。部署前先在测试机确认 Docker 官方 CentOS/RHEL 兼容仓库可正常解析和验签：

```bash
sudo -i
dnf -y install dnf-plugins-core ca-certificates curl rsync jq unzip git tar zstd chrony

dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf makecache
dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

安装后先停止自动启动的服务，再执行 6.3 的数据根目录配置：

```bash
systemctl stop docker docker.socket containerd
```

### 6.2B Ubuntu 24.04 LTS 安装 Docker（备选）

```bash
sudo -i
apt update
apt install -y ca-certificates curl gnupg rsync jq unzip git ufw chrony zstd

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl stop docker docker.socket containerd
```

### 6.3 设置 Docker 数据根目录

停止服务：

```bash
systemctl stop docker docker.socket containerd
```

写入 `/etc/docker/daemon.json`：

```json
{
  "data-root": "/opt/docker/engine",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "5"
  },
  "live-restore": true,
  "userland-proxy": false
}
```

配置 containerd：

```bash
containerd config default > /etc/containerd/config.toml
```

编辑 `/etc/containerd/config.toml` 顶部配置，将：

```toml
root = "/var/lib/containerd"
```

改为：

```toml
root = "/opt/docker/containerd"
```

`state` 保持在 `/run/containerd`，因为它是重启后可重建的运行时状态，不属于持久化数据。

启动并验证：

```bash
systemctl daemon-reload
systemctl enable --now containerd docker

docker info --format 'DockerRootDir={{.DockerRootDir}}'
docker compose version
containerd config dump | sed -n '1,12p'
```

预期：

```text
DockerRootDir=/opt/docker/engine
```

并确认 containerd 的 `root` 为 `/opt/docker/containerd`。

### 6.4 已有 Docker 服务器迁移数据根目录

如果服务器已运行容器，不可直接修改配置后重启。应先维护停机、停止全部容器，再同步数据：

```bash
# 先备份和停止业务
cd /opt/docker-files/xdy/compose
docker compose down
systemctl stop docker docker.socket containerd

rsync -aHAX --numeric-ids /var/lib/docker/ /opt/docker/engine/
rsync -aHAX --numeric-ids /var/lib/containerd/ /opt/docker/containerd/

# 修改 daemon.json 和 containerd config 后启动
systemctl start containerd docker

docker info --format '{{.DockerRootDir}}'
docker ps -a
```

确认所有容器、镜像、网络正常后，再将旧目录重命名保留 7 天；不要立即删除。

---

## 7. 后台应用镜像

### 7.1 Python 依赖

应以现网 `/srv/xdy-admin/` 的实际依赖锁定版本。示例 `requirements.txt`：

```text
Flask==3.1.3
waitress==3.0.2
Jinja2==3.1.6
Werkzeug==3.1.8
cos-python-sdk-v5==1.9.44
```

迁移前必须通过以下命令生成现网精确清单，再审核无用依赖：

```bash
/srv/xdy-admin/.venv/bin/pip freeze > requirements-current.txt
```

### 7.2 Dockerfile.admin

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 10001 xdy \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin xdy

WORKDIR /app
COPY compose/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY admin/app/ /app/
RUN chown -R xdy:xdy /app

USER 10001:10001
EXPOSE 8787

CMD ["python", "app.py"]
```

现网由 `app.py` 内部启动 Waitress 并监听 `127.0.0.1:8787`。容器化时必须将监听地址改为 `0.0.0.0:8787`，但仍只在 Docker 内部网络暴露。

### 7.3 密钥与配置

至少包括：

- Flask `SECRET_KEY`；
- 后台账号密码哈希；
- `TENCENT_SECRET_ID`；
- `TENCENT_SECRET_KEY`；
- `COS_BUCKET`；
- `COS_REGION`；
- `COS_PREFIX`；
- `CDN_BASE`；
- 环境标识 `production`。

原则：

1. 密钥不得写入 Dockerfile、Compose、Git 或镜像层；
2. 密钥文件放在 `/opt/docker-files/xdy/admin/secrets/`，权限 `0600`；
3. 应优先让应用读取环境变量或 `/run/secrets/`；
4. 迁移后轮换 COS 密钥、后台密码和 Flask Session 密钥；
5. 生产与测试环境不得共用 COS 写入凭据。

---

## 8. Docker Compose

在 `/opt/docker-files/xdy/compose/compose.yml` 创建：

```yaml
name: xdy-website

services:
  nginx:
    image: nginx:stable-alpine
    container_name: xdy-nginx
    restart: unless-stopped
    depends_on:
      admin:
        condition: service_healthy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /opt/docker-files/xdy/nginx/conf.d:/etc/nginx/conf.d:ro,Z
      - /opt/docker-files/xdy/nginx/logs:/var/log/nginx:Z
      - /opt/docker-files/xdy/web:/srv/xdy-web:ro,z
      - /opt/docker-files/xdy/certbot/www:/var/www/certbot:ro,z
      - /opt/docker-files/xdy/letsencrypt/etc:/etc/letsencrypt:ro,z
    networks:
      - edge
      - backend
    cpus: 0.50
    mem_limit: 256m
    pids_limit: 128
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD-SHELL", "nginx -t || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

  admin:
    image: xdy-admin:1.0.0
    build:
      context: /opt/docker-files/xdy
      dockerfile: compose/Dockerfile.admin
    container_name: xdy-admin
    restart: unless-stopped
    expose:
      - "8787"
    environment:
      XDY_ENV: production
      XDY_SITE_ROOT: /srv/xdy-web/current
      XDY_DATA_DIR: /data
      XDY_BACKUP_DIR: /backups
    env_file:
      - /opt/docker-files/xdy/admin/secrets/cos.env
    volumes:
      - /opt/docker-files/xdy/web:/srv/xdy-web:z
      - /opt/docker-files/xdy/admin/data:/data:Z
      - /opt/docker-files/xdy/admin/backups:/backups:Z
      - /opt/docker-files/xdy/admin/logs:/logs:Z
      - /opt/docker-files/xdy/admin/secrets/config.json:/app/config.json:ro,Z
      - /opt/docker-files/xdy/admin/secrets/flask-secret:/run/secrets/flask-secret:ro,Z
    networks:
      - backend
    cpus: 1.00
    mem_limit: 768m
    pids_limit: 128
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.create_connection(('127.0.0.1',8787),3); s.close()"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s

  certbot:
    image: certbot/certbot:latest
    container_name: xdy-certbot
    profiles: ["ops"]
    volumes:
      - /opt/docker-files/xdy/certbot/www:/var/www/certbot:z
      - /opt/docker-files/xdy/letsencrypt/etc:/etc/letsencrypt:z
      - /opt/docker-files/xdy/letsencrypt/lib:/var/lib/letsencrypt:Z
    cpus: 0.25
    mem_limit: 256m
    security_opt:
      - no-new-privileges:true

networks:
  edge:
    name: xdy-edge
  backend:
    name: xdy-backend
    internal: true
```

注意：

- OpenCloudOS 默认可能启用 SELinux。示例中的 `z` 表示多个容器共享该挂载标签，`Z` 表示仅当前容器使用；如果企业安全策略不允许 Compose 自动重标记，应由系统管理员使用 `semanage fcontext`/`restorecon` 预先配置标签；
- 生产镜像必须锁定具体版本和镜像 digest，升级时单独验证，不长期使用浮动标签；
- Certbot 示例保留 `latest` 仅用于展示命令，生产应锁定测试过的版本；
- `admin` 不映射宿主机端口；
- Nginx 对网站目录只读，后台对网站目录可写；
- `content.json`、配置、备份和证书均使用绑定挂载，迁移时可直接打包 `/opt/docker-files/xdy/`。

---

## 9. Nginx 配置

### 9.1 首次签证书前的 HTTP 配置

`/opt/docker-files/xdy/nginx/conf.d/xdy.conf`：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name xdy.secondlife.today;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

首次申请证书时，可暂时将 `location /` 改为静态站点或先只启动 HTTP；证书申请成功后切换到完整 HTTPS 配置。

### 9.2 完整 HTTPS 配置

```nginx
limit_req_zone $binary_remote_addr zone=admin_login:10m rate=10r/m;

server {
    listen 80;
    listen [::]:80;
    server_name xdy.secondlife.today;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name xdy.secondlife.today;

    server_tokens off;
    charset utf-8;
    client_max_body_size 50m;

    ssl_certificate /etc/letsencrypt/live/xdy.secondlife.today/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xdy.secondlife.today/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;

    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header X-Frame-Options SAMEORIGIN always;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log warn;

    root /srv/xdy-web/current;
    index index.html;

    location = /sw.js {
        try_files $uri =404;
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    }

    location ~* \\.(?:css|js|png|jpg|jpeg|gif|svg|webp|ico|woff2?)$ {
        try_files $uri =404;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    location ^~ /admin/ {
        proxy_pass http://admin:8787;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        proxy_redirect off;
    }

    location ^~ /api/ {
        proxy_pass http://admin:8787;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
        proxy_redirect off;
    }

    location ~ /\\. {
        deny all;
    }

    location / {
        try_files $uri $uri/ $uri/index.html =404;
        add_header Cache-Control "no-cache";
    }
}
```

上线前应确认：

- 后台路由是否原生包含 `/admin/` 前缀；
- Flask 是否设置 `ProxyFix` 或正确处理 `X-Forwarded-*`；
- 登录、上传、保存、发布、退出均通过 HTTPS 正常；
- 如果正式域名变更，证书路径和 `server_name` 同步修改。

---

## 10. 首次部署流程

### 10.1 准备 DNS 和防火墙

1. 将域名 A/AAAA 记录指向新服务器；
2. 上线前将 DNS TTL 降至 300 秒；
3. 安全组和宿主机防火墙仅开放：
   - `22/tcp`：限制运维 IP；
   - `80/tcp`：证书和 HTTPS 跳转；
   - `443/tcp`：正式访问；
4. 不开放 `8787`、Docker API `2375/2376`。

OpenCloudOS 9.4 使用 firewalld：

```bash
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<运维公网IP>/32" port port="22" protocol="tcp" accept'
firewall-cmd --reload
firewall-cmd --list-all
```

确认新的 SSH 会话可以从运维 IP 登录后，再根据企业策略移除面向所有来源的 `ssh` service。不要在唯一 SSH 会话中直接关闭现有规则，以免锁死服务器。

Ubuntu 使用 UFW：

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from <运维公网IP> to any port 22 proto tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status verbose
```

### 10.2 迁移前备份现网

在旧服务器执行：

```bash
tar --xattrs --acls -czf /root/xdy-site-$(date +%F-%H%M).tar.gz /srv/xdy
tar --xattrs --acls -czf /root/xdy-admin-$(date +%F-%H%M).tar.gz /srv/xdy-admin
cp /etc/caddy/Caddyfile.d/85-xdy.caddyfile /root/
```

另外导出：

- Python 精确依赖；
- 后台配置和密码哈希；
- COS Bucket、Region、上传前缀和 CDN 域名；
- 当前 Git commit；
- 当前域名、证书和 DNS 信息；
- 最近 30 份发布备份。

### 10.3 初始化首个静态版本

```bash
cd /opt/docker-files/xdy/web/releases
RELEASE=$(date +%Y%m%d%H%M%S)
git clone --depth 1 <官网仓库地址> "$RELEASE"
chown -R 10001:10001 "$RELEASE"
ln -sfn "releases/$RELEASE" /opt/docker-files/xdy/web/current
```

注意：`current` 链接相对于 `/opt/docker-files/xdy/web/`，推荐使用相对链接，迁移目录后仍可工作。

### 10.4 准备后台

将现网 `/srv/xdy-admin/` 中经过审核的代码复制到：

```text
/opt/docker-files/xdy/admin/app/
```

将数据分别放入：

```text
content.json  -> /opt/docker-files/xdy/admin/data/content.json
leads.json    -> /opt/docker-files/xdy/admin/data/leads.json
config.json   -> /opt/docker-files/xdy/admin/secrets/config.json
backups/      -> /opt/docker-files/xdy/admin/backups/
```

确认应用中的路径已改为环境变量或容器路径，禁止继续硬编码旧服务器 `/srv/xdy`。

### 10.5 构建后台镜像

```bash
cd /opt/docker-files/xdy/compose
docker compose config
docker compose build --pull admin
docker image inspect xdy-admin:1.0.0 >/dev/null
```

### 10.6 首次申请证书

先启动 HTTP Nginx：

```bash
docker compose up -d nginx admin
```

申请证书：

```bash
docker compose --profile ops run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email <运维邮箱> \
  --agree-tos --no-eff-email \
  -d xdy.secondlife.today
```

切换完整 HTTPS 配置后：

```bash
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

### 10.7 启动和验收

```bash
cd /opt/docker-files/xdy/compose
docker compose up -d
docker compose ps
docker compose logs --tail=200 nginx admin
```

验收：

```bash
curl -I http://xdy.secondlife.today/
curl -I https://xdy.secondlife.today/
curl -I https://xdy.secondlife.today/web/
curl -I https://xdy.secondlife.today/admin/
```

浏览器验收至少覆盖：

- Windows：Chrome、Edge、Firefox；
- macOS：Safari、Chrome；
- iPhone：Safari；
- Android：Chrome；
- 1440、1024/768、390 三类视口；
- 首页、关于企业、产品、运营、加盟、资讯；
- 设计体系、品牌手册、小程序预览；
- 后台登录、上传图片、保存、发布、退出；
- 加盟表单提交、`/api/*` 接口和 `leads.json` 写入；
- 发布后前台内容更新且旧版已写入备份。

---

## 11. 日常发布流程

### 11.1 内容更新

运营人员仅通过后台更新内容：

1. 登录 `/admin/`；
2. 修改文字或上传图片；
3. 保存草稿；
4. 预览；
5. 发布；
6. 检查前台和移动端；
7. 确认备份目录生成新版本。

原则：后台管理的字段不得只手工修改最终 HTML，否则下一次后台发布会被 `content.json + Jinja` 覆盖。

### 11.2 代码版本发布

推荐脚本逻辑：

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE=/opt/docker-files/xdy/web
REPO=<官网仓库地址>
RELEASE=$(date +%Y%m%d%H%M%S)

mkdir -p "$BASE/releases/$RELEASE"
git clone --depth 1 "$REPO" "$BASE/releases/$RELEASE"
chown -R 10001:10001 "$BASE/releases/$RELEASE"

# 验证关键文件
for f in index.html styles.css web/index.html web/responsive.css web/responsive.js; do
  test -f "$BASE/releases/$RELEASE/$f"
done

# 原子切换软链接
ln -sfn "releases/$RELEASE" "$BASE/current.new"
mv -Tf "$BASE/current.new" "$BASE/current"

# 让后台内容源重新生成被管理的页面
# docker compose exec admin python render.py publish

docker exec xdy-nginx nginx -t
docker exec xdy-nginx nginx -s reload
```

实际执行前，应确认后台 `render.py publish` 的入口和目标路径；如果新版模板发生变化，必须先在测试环境用现网 `content.json` 渲染并比较结果。

### 11.3 回滚

查看版本：

```bash
ls -lt /opt/docker-files/xdy/web/releases
readlink -f /opt/docker-files/xdy/web/current
```

切换旧版：

```bash
cd /opt/docker-files/xdy/web
ln -sfn releases/<previous-release> current.new
mv -Tf current.new current
docker exec xdy-nginx nginx -t
docker exec xdy-nginx nginx -s reload
```

如果回滚涉及后台内容，同时恢复对应时间点的：

- `content.json`；
- 被发布的 HTML；
- 后台模板版本；
- 必要时的图片 URL。

仅回滚 HTML、不回滚 `content.json`，下一次发布可能再次覆盖旧版。

---

## 12. 证书自动续期

创建 `/opt/docker-files/xdy/scripts/renew-cert.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/docker-files/xdy/compose

docker compose --profile ops run --rm certbot renew \
  --webroot -w /var/www/certbot

docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

```bash
chmod 750 /opt/docker-files/xdy/scripts/renew-cert.sh
```

使用 root Cron 每天执行一次：

```cron
17 3 * * * /opt/docker-files/xdy/scripts/renew-cert.sh >> /opt/docker-files/xdy/nginx/logs/certbot-renew.log 2>&1
```

每月检查一次证书到期时间：

```bash
openssl s_client -connect xdy.secondlife.today:443 -servername xdy.secondlife.today </dev/null 2>/dev/null \
  | openssl x509 -noout -dates -issuer -subject
```

---

## 13. 备份与恢复

### 13.1 备份范围

必须备份：

- `/opt/docker-files/xdy/admin/data/`（含 `content.json`、`leads.json`）；
- `/opt/docker-files/xdy/admin/secrets/`；
- `/opt/docker-files/xdy/admin/backups/`；
- `/opt/docker-files/xdy/compose/`；
- `/opt/docker-files/xdy/nginx/conf.d/`；
- `/opt/docker-files/xdy/letsencrypt/`；
- 当前发布版本和最近 2–3 个 release；
- Git 仓库由远程代码平台冗余保存；
- 腾讯云 COS 开启版本控制，并按业务要求配置生命周期。

不建议长期备份：

- Nginx 访问日志全部历史；
- `/opt/docker/` 整目录；
- 可从镜像仓库重新拉取的镜像层。

### 13.2 备份策略

- 每日增量/打包：保留 7 天；
- 每周全量：保留 4 周；
- 每月全量：保留 6–12 个月；
- 至少一份备份位于另一台服务器或对象存储；
- 密钥与 `leads.json` 备份必须加密，并限制备份读取人员；
- 每季度实际执行一次恢复演练。

### 13.3 备份脚本示例

```bash
#!/usr/bin/env bash
set -euo pipefail

SRC=/opt/docker-files/xdy
DST="$SRC/backup/daily"
STAMP=$(date +%F-%H%M%S)
OUT="$DST/xdy-$STAMP.tar.zst"

mkdir -p "$DST"
tar --xattrs --acls \
  --exclude="$SRC/nginx/logs" \
  --exclude="$SRC/backup" \
  --exclude="$SRC/web/releases" \
  -C /opt/docker-files xdy \
  | zstd -T0 -10 -o "$OUT"

find "$DST" -type f -name 'xdy-*.tar.zst' -mtime +7 -delete
sha256sum "$OUT" > "$OUT.sha256"
```

备份完成后应上传到异机/COS 的私有备份 Bucket，不可放在官网公开 Bucket。

### 13.4 恢复演练

1. 新建临时服务器；
2. 安装相同主版本的 Docker/Compose；
3. 配置 `/opt/docker/` 根目录；
4. 恢复 `/opt/docker-files/xdy/`；
5. 恢复密钥文件权限；
6. `docker compose config`；
7. 构建/拉取镜像；
8. 启动容器；
9. 使用临时域名或 hosts 验证；
10. 验证后台发布、COS 上传、证书、前台页面；
11. 记录实际 RTO/RPO。

建议目标：

- RPO：24 小时以内；
- RTO：2 小时以内；
- 内容发布前备份可将单次错误回退缩短到 10 分钟以内。

---

## 14. 日志、监控和告警

### 14.1 日志

- Docker 容器日志限制为 `20 MB × 5`；
- Nginx 文件日志使用 logrotate；
- 后台应用日志避免记录密码、Session、COS Secret；
- 保留错误日志 30–90 天，访问日志按隐私与合规要求处理。

`/etc/logrotate.d/xdy-nginx` 示例：

```text
/opt/docker-files/xdy/nginx/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        /usr/bin/docker exec xdy-nginx nginx -s reopen >/dev/null 2>&1 || true
    endscript
}
```

### 14.2 最低监控项

- 首页 HTTPS 状态和响应时间；
- `/admin/` 状态；
- TLS 证书剩余天数；
- 容器状态和重启次数；
- CPU、内存、磁盘、inode；
- `/opt/docker/` 和 `/opt/docker-files/` 使用率；
- Nginx 5xx；
- 后台发布失败；
- COS 上传失败；
- 每日备份是否生成、大小是否异常、校验是否通过。

告警阈值建议：

- 磁盘使用率 > 75% 预警，> 85% 严重；
- 内存连续 10 分钟 > 85%；
- 容器 10 分钟内重启 3 次；
- HTTPS 连续 3 次失败；
- 证书剩余 < 21 天；
- 24 小时未生成备份。

---

## 15. 安全基线

1. SSH 禁止密码登录，使用密钥；
2. 禁止 root 直接远程登录；
3. 22 端口限制运维 IP；
4. 不开放 Docker TCP API；
5. 后台仅 HTTPS；
6. 后台密码使用强哈希，定期轮换；
7. Flask `SECRET_KEY` 使用至少 32 字节随机值；
8. COS 子账号遵循最小权限，仅允许指定 Bucket/前缀；
9. COS Secret 不写入 Git、镜像或日志；
10. Nginx、Python 基础镜像定期更新，但先在测试环境验证；
11. 容器启用 `no-new-privileges`，后台使用非 root UID；
12. 宿主机按月安装安全更新；
13. 管理后台增加登录失败限流和审计日志；
14. 发布前对上传文件校验 MIME、后缀、大小和文件名；
15. 备份文件加密并做异地副本；
16. 域名、云服务器、COS、代码仓库均开启 MFA。

---

## 16. 数据库升级判断

当前 `content.json + leads.json` 文件方案继续使用的条件：

- 运营账号数量少；
- 同一时间基本只有一人编辑；
- 页面内容规模有限；
- 不需要复杂查询；
- 不需要多级审核流；
- 发布前自动备份可靠。

满足以下任意 2–3 项时，建议迁移 PostgreSQL：

- 多人同时编辑；
- 需要草稿、审核、发布三段工作流；
- 需要字段级权限；
- 需要按时间查询任意历史版本；
- 内容量明显增长并涉及大量结构化关联；
- 需要开放 API 给小程序、第三方平台或门店系统；
- 文件锁和合并冲突开始影响运营。

迁移时建议：

1. PostgreSQL 独立容器或云数据库；
2. 数据目录位于 `/opt/docker-files/postgres/data/`；
3. 数据库仅加入内部网络；
4. 使用专用低权限用户；
5. 每日全量 + 增量/WAL 备份；
6. 后台迁移完成后，前台仍保持静态发布模式，避免把数据库故障传导给公开官网。

---

## 17. 上线检查清单

### 17.1 系统

- [ ] DockerRootDir 为 `/opt/docker/engine`；
- [ ] containerd root 为 `/opt/docker/containerd`；
- [ ] 所有绑定挂载均位于 `/opt/docker-files/`；
- [ ] `docker compose config` 无错误；
- [ ] 容器均为 healthy；
- [ ] 后台 8787 未映射公网；
- [ ] 防火墙只开放必要端口；
- [ ] 时区和 NTP 正常；
- [ ] 日志轮转已配置。

### 17.2 业务

- [ ] 首页及所有一级页面 HTTP 200；
- [ ] 桌面、平板、手机无横向溢出；
- [ ] 主流浏览器显示正常；
- [ ] PWA Service Worker 更新正常；
- [ ] COS 图片/视频无 4xx；
- [ ] 后台登录正常；
- [ ] 内容保存和发布正常；
- [ ] 图片上传 COS 正常；
- [ ] 发布前备份正常；
- [ ] 回滚演练正常。

### 17.3 安全与备份

- [ ] TLS 证书有效且自动续期；
- [ ] 后台密码和密钥已轮换；
- [ ] COS 权限最小化；
- [ ] 异地备份已完成；
- [ ] 备份校验值已生成；
- [ ] 已完成一次实际恢复演练；
- [ ] 监控和告警接收人明确。

---

## 18. 推荐实施顺序

### 阶段一：资料固化

1. 导出现网 `/srv/xdy`；
2. 导出现网 `/srv/xdy-admin`；
3. 锁定 Python 依赖；
4. 记录 Caddy 路由；
5. 记录 COS 配置项名称；
6. 验证 `content.json` 可独立重渲染前台。

### 阶段二：测试环境容器化

1. 安装 Docker 并配置 `/opt/docker/`；
2. 创建 `/opt/docker-files/xdy/`；
3. 构建后台镜像；
4. 启动 Nginx、Admin；
5. 使用测试域名和测试 COS 前缀；
6. 完成发布、备份、回滚、跨屏兼容测试。

### 阶段三：生产切换

1. 冻结旧后台内容更新；
2. 做最后一次全量备份；
3. 同步最新 `content.json`、模板和发布文件；
4. 新服务器启动并做 hosts 验证；
5. 切换 DNS；
6. 观察 24–48 小时；
7. 旧服务器只读保留至少 7 天。

### 阶段四：运维标准化

1. 配置自动证书续期；
2. 配置日志轮转；
3. 配置每日备份和异地上传；
4. 配置监控和告警；
5. 每季度恢复演练；
6. 每半年复核资源和数据库升级必要性。

---

## 19. 迁移风险

| 风险 | 后果 | 控制措施 |
|---|---|---|
| 仅复制静态 HTML，遗漏 `content.json` | 后续无法继续编辑或发布 | 将后台数据列为一级备份对象 |
| 手工修改 HTML 未同步模板 | 下次发布覆盖改动 | 模板、内容源、最终 HTML 三者一致性检查 |
| 只配置 Docker data-root | containerd 数据仍写入 `/var/lib/containerd` | 同时配置 containerd root |
| 后台端口暴露公网 | 绕过 Nginx/TLS/限流 | 仅 `expose`，不使用 `ports` |
| COS 密钥进入镜像或 Git | 媒体资产和账户风险 | Secret 文件、最小权限、迁移后轮换 |
| 证书续期后 Nginx 未 reload | 继续使用旧证书 | 续期脚本中执行 `nginx -t` 和 reload |
| 日志无限增长 | 磁盘占满、服务中断 | Docker 日志限制 + logrotate + 磁盘告警 |
| 直接删除旧服务器 | 迁移遗漏无法补救 | 只读保留至少 7 天 |
| 未做实际恢复演练 | 备份存在但不可用 | 每季度恢复到临时机验证 |

---

## 20. 最终推荐

熊大爷官网当前最合适的生产架构是：

```text
Ubuntu 24.04 LTS
└── Docker Engine + containerd
    ├── /opt/docker/engine
    ├── /opt/docker/containerd
    └── Docker Compose
        ├── Nginx：静态站、HTTPS、反向代理
        ├── Flask + Waitress：轻量内容后台
        └── Certbot：证书签发与续期

持久化：/opt/docker-files/xdy/
媒体：腾讯云 COS/CDN
内容主数据：content.json + leads.json
代码版本：Git
基础版本：不部署数据库、Redis 或 SQLite
推荐服务器：4 vCPU / 8 GB RAM / 100 GB SSD / 10 Mbps+
```

该方案保持前台“无后端依赖”的高可用特征，同时将后台、配置、证书、备份和发布流程标准化，满足后续迁移、扩容和故障恢复要求。
