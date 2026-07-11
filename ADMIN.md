# 官网内容管理后台（轻量版）

运营人员通过后台修改官网文字与图片，无需改代码。入口：<https://xdy.secondlife.today/admin/>（账号找 @米开朗基罗 或管理员领取）。

## 架构

```
浏览者 ──> Caddy ──> /admin/*  反代 127.0.0.1:8787（Flask + waitress，systemd: xdy-admin）
                └──> 其余路径  静态 file_server（/srv/xdy）

后台发布流程：
content.json（结构化内容） + templates/web.html.j2（Jinja 模板）
        │  点「保存并发布」
        ▼
/srv/xdy/web/index.html（重新渲染的纯静态页，前台零后端依赖）
```

- 服务代码在服务器 `/srv/xdy-admin/`（app.py / render.py / content.json / templates/），不在本仓库——避免被静态服务器直接暴露源码。
- 图片在后台上传后自动进腾讯云 COS（`xdy/web/uploads/` 前缀），表单里回填 CDN URL。
- 每次发布前自动备份旧版 index.html 到 `/srv/xdy-admin/backups/`（保留最近 30 份）。
- 登录：单账号 + 密码哈希（`config.json`），会话走 Flask session；仅 HTTPS。

## 可编辑板块

首屏 Hero / 数据带 / 品牌故事 / 产品（饺子 + 云吞面条卡片，可增删）/ 门店空间 / 品牌大事纪（可增删）/ 加盟（要点 + 流程步骤，可增删）/ 页脚站点信息 / SEO 标题描述。

字段里允许简单标记：标题换行写 `<br>`，导语强调写 `<em>…</em>`。

## 给后续接手的开发

- **内容模型就是 `content.json`**——要迁移到你们自己的 CMS，把这个 JSON 的 schema 搬过去、按 `web.html.j2` 的槽位渲染即可，前台 HTML/CSS 不用动。
- 重渲染命令行：`/srv/xdy-admin/.venv/bin/python /srv/xdy-admin/render.py publish`
- 服务管理：`systemctl {status,restart} xdy-admin`；Caddy 路由在 `/etc/caddy/Caddyfile.d/85-xdy.caddyfile`。
- 手工改了 `web/index.html` 的话注意：下次后台「发布」会以 content.json 为准覆盖它——静态文件的改动要同步进 content.json 或模板。
