# 品牌资源目录 / Brand Assets

将你的团队品牌图片放在此目录下，替换对应文件即可自定义外观。

## 必需文件

| 文件名 | 用途 | 建议尺寸 |
|--------|------|----------|
| `team-logo.png` | 导航栏 Logo + Favicon 来源 | 256×256 或更大，正方形 PNG |
| `background-main.jpg` | 首页背景 | 1920×1080，风景/抽象 |

## 可选文件

| 文件名 | 用途 | 建议尺寸 |
|--------|------|----------|
| `dashboard-background.jpg` | 仪表盘页面背景 | 1920×1080 |
| `usage-background.jpg` | 使用记录页面背景 | 1920×1080 |
| `quota-background.jpg` | 额度页面背景 | 1920×1080 |
| `relay-station-background.jpg` | 首页 Hero 区域背景 | 1920×1080 |
| `team-motto.jpg` | 团队格言卡片背景 | 1200×400 |

## 自动生成的文件（部署时生成）

| 文件名 | 用途 |
|--------|------|
| `favicon-32x32.png` | 浏览器标签页图标 |
| `apple-touch-icon.png` | iOS 书签图标 |

这些文件由 `team-logo.png` 自动生成，见部署脚本。

## 提示

- 背景图建议使用暗色调或带有半透明遮罩效果的图片，因为上层有白色半透明覆盖层
- Logo 建议使用透明背景的 PNG
- 如果不需要某个背景，可以放一张纯色图片或删除文件（会 fallback 到纯色渐变）
