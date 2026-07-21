# 熊大爷现包饺子 · 品牌设计体系 Brand Design System

四川联拓食品集团「熊大爷现包饺子」品牌升级设计体系与全套应用物料。
Live: https://xdy.secondlife.today

## 结构

| 目录 | 内容 |
|---|---|
| `ds/` | 设计体系 v3.1：总纲 / 色彩 / 字体 / 标识 / 母题 / 组件 / 摄影与 IP |
| `manual/` | 品牌手册 3.1（21 页 · deck-stage 阅读器） |
| `web/` | 品牌官网 v2（单页五屏） |
| `cards/` | 名片与事务用品（含出血与印制规格） |
| `merch/` | PANDA YEAH 2.0 设定稿 + 周边 12 类 |
| `motion/` | 动效规格 + 30s 品牌片《现包》 |
| `store/` | 门店五触点视觉规范 + AI 生图对齐说明 |
| `anime/` | IP 动漫化：角色圣经 / 四风格定妆 / 分镜 / 样片 |
| `miniapp/` | 点餐小程序 UI 设计（五屏 + 组件规范） |
| `pwa/` + `manifest.webmanifest` + `sw.js` | PWA 支持 |

## 设计基石（DS v3.1）

面粉为纸 `#FCFBF8` · 暖墨为字 `#241E1B` · 雅金为笔 `#7D5F17/#C4993F` · 绛红为印 `#9F3B3B`（一屏一印 ≤5%）。
共享 tokens 在 `styles.css`。

## 系统与部署

- Docker 化系统架构、组件清单、资源建议、部署/备份/迁移流程：[`docs/deployment/xdy-website-system-deployment.md`](docs/deployment/xdy-website-system-deployment.md)

## 媒体资源

图片/视频统一走腾讯云 COS（前缀 `xdy/`，路径与仓库一一镜像），HTML 内为绝对地址；
仓库内 `*.mp4` 不入库（见 `.gitignore`），源片在服务器 `/srv/xdy` 与 COS。

—— Maintained by 米开朗基罗 (Syfo agent) & Tony
