import AppKit
import Foundation

// 这个脚本把项目里的 SVG 图标转成 Android 各种屏幕密度需要的 PNG。
// Android 工程是自动生成目录，所以每次构建前都重新写入图标，避免同步时被默认图标覆盖。

let scriptURL = URL(fileURLWithPath: #filePath).standardizedFileURL
let mobileURL = scriptURL.deletingLastPathComponent().deletingLastPathComponent()
let projectURL = mobileURL.deletingLastPathComponent()
let sourceURL = projectURL.appending(path: "icons/app-icon.svg")
let resourceURL = mobileURL.appending(path: "android/app/src/main/res")
let capacitorConfigURL = mobileURL.appending(path: "capacitor.config.json")

guard
    let configData = try? Data(contentsOf: capacitorConfigURL),
    let config = try? JSONSerialization.jsonObject(with: configData) as? [String: Any],
    let appName = config["appName"] as? String,
    let appId = config["appId"] as? String
else {
    fatalError("无法从 capacitor.config.json 读取应用名称和标识。")
}

guard let sourceImage = NSImage(contentsOf: sourceURL) else {
    fatalError("无法读取应用图标：\(sourceURL.path)")
}

// Android 的 launcher 位图按 mdpi 到 xxxhdpi 分别需要这些像素尺寸。
let densities: [(folder: String, launcher: Int, adaptive: Int)] = [
    ("mipmap-mdpi", 48, 108),
    ("mipmap-hdpi", 72, 162),
    ("mipmap-xhdpi", 96, 216),
    ("mipmap-xxhdpi", 144, 324),
    ("mipmap-xxxhdpi", 192, 432)
]

func pngData(size: Int) -> Data {
    let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: size,
        pixelsHigh: size,
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    )!

    NSGraphicsContext.saveGraphicsState()
    let context = NSGraphicsContext(bitmapImageRep: bitmap)!
    context.imageInterpolation = .high
    NSGraphicsContext.current = context
    sourceImage.draw(in: NSRect(x: 0, y: 0, width: size, height: size))
    context.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()

    return bitmap.representation(using: .png, properties: [:])!
}

for density in densities {
    let directoryURL = resourceURL.appending(path: density.folder)
    try FileManager.default.createDirectory(at: directoryURL, withIntermediateDirectories: true)

    // 旧版 Android 直接使用完整图标；新版 Android 会使用下面的自适应图标前景图。
    let launcherPNG = pngData(size: density.launcher)
    try launcherPNG.write(to: directoryURL.appending(path: "ic_launcher.png"))
    try launcherPNG.write(to: directoryURL.appending(path: "ic_launcher_round.png"))

    let foregroundPNG = pngData(size: density.adaptive)
    try foregroundPNG.write(to: directoryURL.appending(path: "ic_launcher_foreground.png"))
}

// 自适应图标的底色跟 SVG 一致，系统会按手机桌面选择的图标形状进行裁切。
let backgroundXML = """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#12352D</color>
</resources>
"""
try backgroundXML.write(
    to: resourceURL.appending(path: "values/ic_launcher_background.xml"),
    atomically: true,
    encoding: .utf8
)

// Capacitor 同步网页时不会自动改已有 Android 工程的安装名称，所以从同一份配置写入桌面显示名。
let stringsXML = """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">\(appName)</string>
    <string name="title_activity_main">\(appName)</string>
    <string name="package_name">\(appId)</string>
    <string name="custom_url_scheme">\(appId)</string>
</resources>
"""
try stringsXML.write(
    to: resourceURL.appending(path: "values/strings.xml"),
    atomically: true,
    encoding: .utf8
)

print("Android 应用图标和安装名称已根据项目配置生成：\(appName)")
