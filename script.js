// 先从项目里的 JSON 文件读取密码，方便后面换成自动更新的数据。
const DATA_URL = "./codes.json";


// 把同一张地图的密码同步到顶部入口和下方详情卡片。
function updateMapCode(mapId, code) {
    const tab = document.querySelector(`.map-tabs label[for="${mapId}"]`);
    const detail = document.getElementById(`${mapId}-entry`);

    if (!tab || !detail) {
        console.warn(`没有找到地图对应的页面元素：${mapId}`);
        return;
    }

    // 密码按文本写入，保留 0257 这样的前导零。
    const tabCode = tab.querySelector("span:last-child");
    const detailCode = detail.querySelector(".password p");

    if (!tabCode || !detailCode) {
        console.warn(`地图缺少密码显示位置：${mapId}`);
        return;
    }

    tabCode.textContent = code;
    detailCode.textContent = code;
}


// 先检查数据格式，再一次性更新页面，避免只改到一部分地图。
function showDailyCodes(data) {
    const requiredMaps = [
        "zero-dam",
        "longbow-creek",
        "buckshot",
        "space-station",
        "tide-prison",
        "az3"
    ];

    if (!data || !data.maps) {
        throw new Error("codes.json 里没有找到 maps 数据");
    }

    for (const mapId of requiredMaps) {
        if (!/^\d{4}$/.test(data.maps[mapId] ?? "")) {
            throw new Error(`请检查 ${mapId} 的密码，密码需要是四位数字`);
        }
    }

    for (const mapId of requiredMaps) {
        updateMapCode(mapId, data.maps[mapId]);
    }
}


// 页面打开后读取 codes.json；读取失败时保留 HTML 里原来的密码。
async function loadDailyCodes() {
    try {
        const response = await fetch(DATA_URL, { cache: "no-store" });

        if (!response.ok) {
            throw new Error(`读取 codes.json 失败：HTTP ${response.status}`);
        }

        const data = await response.json();
        showDailyCodes(data);
    } catch (error) {
        console.error("每日密码没有加载成功：", error);
    }
}


// defer 会等 HTML 解析完成后再运行，所以这里可以直接找到页面元素。
loadDailyCodes();
