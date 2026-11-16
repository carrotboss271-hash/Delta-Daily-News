// 用 Node 自带的文件工具复制网页资源，不用再安装额外的复制插件。
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";

// 先从当前脚本的位置往外找，避免命令从不同目录运行时找错路径。
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

// 这个脚本放在 mobile/scripts 里，网页原文件在仓库根目录。
const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const mobileDirectory = resolve(scriptDirectory, "..");
const websiteDirectory = resolve(mobileDirectory, "..");
const outputDirectory = resolve(mobileDirectory, "www");
const liveCodesUrl = "https://carrotboss271-hash.github.io/Delta-Daily-News/codes.json";

// 每次准备资源时先清理旧副本，避免网页删掉的图片还留在应用包里。
await rm(outputDirectory, { recursive: true, force: true });

// 重新建一个空的资源目录，后面复制进去的就是这次准备的网页版本。
await mkdir(outputDirectory, { recursive: true });

// 入口、样式、交互脚本和密码数据是页面运行时会直接用到的文件。
for (const fileName of ["index.html", "style.css", "script.js", "manifest.webmanifest", "codes.json"]) {
  await cp(resolve(websiteDirectory, fileName), resolve(outputDirectory, fileName));
}

// 图片和图标按目录整体复制，保持网页里写的相对路径不变。
for (const directoryName of ["images", "icons"]) {
  await cp(resolve(websiteDirectory, directoryName), resolve(outputDirectory, directoryName), {
    recursive: true
  });
}

// 应用打开时从 Pages 获取最新密码；本地 codes.json 仍保留作断网备用。
const appHtmlPath = resolve(outputDirectory, "index.html");
const appHtml = await readFile(appHtmlPath, "utf8");
const scriptTag = '    <script src="script.js" defer></script>';
const appScriptTag = `    <script>window.DAILY_CODES_URL = "${liveCodesUrl}";</script>\n${scriptTag}`;

if (!appHtml.includes(scriptTag)) {
  throw new Error("index.html 里没有找到 script.js 标签，无法设置移动端的在线密码地址。");
}

await writeFile(appHtmlPath, appHtml.replace(scriptTag, appScriptTag), "utf8");

// 命令行里看到这句话，就表示网页资源已经准备好，可以交给 Capacitor。
console.log("网页资源已复制到 mobile/www。");
