# 三角洲每日资讯移动端

这个目录用 Capacitor 把仓库根目录里的网页放进 Android / iOS 应用。移动端文件都放在这里，GitHub Pages 继续使用仓库根目录的网页。

## 文件分别负责什么

- `package.json`：记录 Capacitor 依赖，以及准备网页、生成原生工程和同步资源的命令。
- `capacitor.config.json`：应用名称、应用标识和网页资源目录等 Capacitor 设置。
- `scripts/prepare-web.mjs`：把根目录的 HTML、CSS、JavaScript、密码 JSON、图片和图标复制到 `www`。
- `scripts/generate-android-icons.swift`：把 `icons/app-icon.svg` 转成 Android 各种尺寸的桌面图标，并从 Capacitor 配置同步安装名称。
- `.gitignore`：忽略依赖、生成目录和本机签名文件，避免把这些内容提交到 GitHub。

`package.json` 和 `capacitor.config.json` 必须保持标准 JSON 格式，里面不能插入注释。每个字段的用途写在这里，脚本里的处理步骤则写在 `.mjs` 注释中。

## 命令是做什么的

- `npm install`：下载项目需要的 Capacitor 工具和 Android / iOS 平台依赖。
- `npm run prepare:web`：重新复制最新网页文件到 `www`。
- `npm run android:add`：准备网页文件，并创建 Android 原生工程。
- `npm run ios:add`：准备网页文件，并创建 iOS 原生工程。
- `npm run android:sync`：把修改后的网页文件同步到 Android 工程。
- `npm run ios:sync`：把修改后的网页文件同步到 iOS 工程。
- `npm run android:open`：在 Android Studio 中打开 Android 工程。
- `npm run ios:open`：在 Xcode 中打开 iOS 工程。

## 构建前需要

- Node.js 22 或更新版本，并包含 npm。
- Android：需要 Android SDK 命令行工具、平台工具、对应 API 平台和 Build Tools。Android Studio 不是必须的，但它能自动安装这些依赖；也可以只下载 Android 官方命令行工具并用 VS Code 终端配置。
- iPhone：使用 Mac 安装 Xcode。

## 这台 Mac 的本地环境

Node/npm、Temurin JDK 和 Android SDK 已放在 `mobile/.tools/`，只供这台 Mac 本地构建并已加入忽略列表，不会推送到 GitHub。VS Code 任务会直接调用这些工具。

当前可安装的调试 APK 放在 `mobile/release/三角洲每日资讯-debug.apk`。`release/` 也已忽略，不会被误推到仓库。

## 在 VS Code 里操作

仓库根目录的 `.vscode/tasks.json` 已经准备了移动端任务。打开命令面板，选择 **Tasks: Run Task**，再选要运行的任务：

1. `三角洲移动端：安装依赖`
2. `三角洲移动端：生成 Android 工程`
3. `三角洲移动端：构建调试 APK`

网页修改后，先运行 `三角洲移动端：同步网页资源`，再重新构建 APK。VS Code 负责编辑和启动命令，实际编译由 Capacitor、Gradle 和 Android SDK 完成。

构建任务会先运行 `android:icons`，再编译 APK；替换仓库根目录的 `icons/app-icon.svg` 可换图标，修改 `capacitor.config.json` 里的 `appName` 可换安装名称。

## 首次生成 Android 工程

如果暂时不用 VS Code 任务，也可以在终端进入 `mobile` 目录后执行：

```sh
npm install
npm run android:add
npm run android:open
```

调试 APK 默认会生成在 `mobile/android/app/build/outputs/apk/debug/app-debug.apk`，可以复制到安卓手机安装查看。构建前可先运行 `npm run android:icons` 更新桌面图标。若不使用 Android Studio，需要先用 Android 官方命令行工具装好 SDK 和 Build Tools。

## 首次生成 iOS 工程

在终端进入 `mobile` 目录后执行：

```sh
npm install
npm run ios:add
npm run ios:open
```

## 后续修改网页

修改仓库根目录网页后，在 `mobile` 目录运行 `npm run android:sync` 或 `npm run ios:sync`，再用 Android Studio 或 Xcode 重新构建应用。

## 每日密码更新

准备脚本会让应用启动时读取 GitHub Pages 上的 `codes.json`，同时把本地副本带进安装包作断网备用。在线数据更新后，已安装的应用下次打开就会读取新密码，不需要重新打包 APK。
