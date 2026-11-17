# 三角洲每日资讯

一个查询《三角洲行动》每日地图密码和点位的静态网页。打开页面即可查看六张地图的四位密码，点击地图名称可查看对应的点位说明和配图。

[打开三角洲每日资讯](https://carrotboss271-hash.github.io/Delta-Daily-News/)

## 项目功能

- **每日密码**：集中展示零号大坝、长弓溪谷、巴克什、航天基地、潮汐监狱和 AZ3 的密码。
- **点位查询**：切换地图后，页面会显示对应的文字说明、参考图片和密码。例如，航天基地的点位在工业组装楼二楼。
- **手机式布局**：网页在桌面端以最大 420 像素的宽度居中显示，六张地图排成两列。屏幕更窄时，内容区随窗口收缩。
- **移动端访问**：网页配置了主屏图标和独立窗口显示。项目也可通过 Capacitor 打包为 Android 或 iOS 应用，启动时读取线上密码，联网请求失败时可读取安装包内的备用数据。

## 开发方式

1. **搭建页面**：用 HTML 编写地图入口和详情卡片。每个入口通过 `label` 关联一个单选框，再用 CSS 的 `:checked` 状态切换详情，默认显示零号大坝。
2. **接入数据**：用 JavaScript 请求 `codes.json`，确认六张地图的密码都是四位数字后，再同步更新顶部入口和详情卡片。Python 脚本负责调用每日密码 API、转换地图 ID 并生成网页所需的 JSON。
3. **自动更新与部署**：GitHub Actions 将每日密码任务安排在北京时间 04:05，也支持手动运行。任务使用 GitHub Actions Secret 中的 `DELTA_API_KEY` 请求 API，并提交更新后的数据。任务成功后，GitHub Pages 部署工作流读取最新的 `master` 分支并发布。
4. **复用网页打包移动端**：Node.js 脚本将网页、图片和备用密码复制到 `mobile/www`，并在应用入口配置线上密码地址。Capacitor 再将这些资源同步到 Android 或 iOS 工程。

## 遇到的问题与解决过程

| 问题 | 用什么工具排查、怎么解决 |
| --- | --- |
| 第二天仓库里的密码已更新，网页和手机应用仍显示前一天的密码 | 对照 GitHub Actions 运行记录、仓库里的 `codes.json` 和浏览器访问的线上文件，发现自动提交后没有新的 Pages 部署。更新任务用 `GITHUB_TOKEN` 推送，未触发原先监听 `push` 的部署流程。给部署工作流增加 `workflow_run` 触发条件，让密码更新任务成功后部署最新的 `master`。推送修复后，已确认 Pages 部署成功，并核对了线上数据。 |
| 部署成功后，直接打开线上 JSON 一度仍看到旧数据 | 在浏览器中给 JSON 地址加查询参数绕过缓存，确认线上已发布新数据。网页和应用的在线请求使用 `fetch(..., { cache: "no-store" })`，以避开浏览器本地缓存。 |
| 推送双列样式后，线上仍显示六列 | 对照 `master` 的 `style.css` 和浏览器中的布局，确认新版样式已提交。GitHub Actions 日志显示 Pages 发布步骤未找到 `github-pages` 构建产物。同一次运行重跑后，发布步骤又查到两个同名产物。部署配置现在使用运行尝试编号为每次上传命名，发布步骤按相同名称查找对应的产物。 |
| 密码可能以 0 开头，接口数据也可能缺少地图 | Python 和 JavaScript 都校验四位数字，密码以字符串保存和显示，保留 `0257` 这类前导零。缺少有效密码或 API 明确标记为非当天数据时，Python 脚本会报错并保留已有文件。 |

GitHub Actions 的定时任务实际启动时间可能晚于配置时间。排查更新延迟时，可以先检查密码更新任务是否启动，再查看对应的 Pages 部署记录。[查看 Actions 运行记录](https://github.com/carrotboss271-hash/Delta-Daily-News/actions)

## 本地开发

在仓库根目录启动静态服务器，然后打开 [http://localhost:8000](http://localhost:8000)：

```sh
python3 -m http.server 8000
```

本地页面读取仓库里的 `codes.json`，预览页面无需 API 密钥。维护每日更新时，可在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 配置 `DELTA_API_KEY`，再从 **Actions → 每日更新地图密码** 手动运行。

| 路径 | 用途 |
| --- | --- |
| [`index.html`](index.html)、[`style.css`](style.css)、[`script.js`](script.js) | 页面结构、地图切换、样式和密码加载 |
| [`codes.json`](codes.json)、[`scripts/update_codes.py`](scripts/update_codes.py) | 密码数据及 API 更新脚本 |
| [`.github/workflows/`](.github/workflows/) | 每日数据更新和 GitHub Pages 部署 |
| [`manifest.webmanifest`](manifest.webmanifest)、[`icons/`](icons/) | 主屏入口配置和图标 |
| [`mobile/`](mobile/) | Capacitor 工程配置和打包脚本。构建步骤见 [移动端 README](mobile/README.md) |
