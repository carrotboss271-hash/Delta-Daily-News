"""从每日密码 API 获取数据，并整理成网页使用的 codes.json。"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo


API_URL = "https://api.dwoyun.com/api/sjz/mrmm/get"
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "codes.json"

# API 地图 ID 和网页单选框 ID 的对应关系。
MAP_ID_TRANSLATION = {
    "linghao_daba": "zero-dam",
    "changgong_xigu": "longbow-creek",
    "bakeshen": "buckshot",
    "hangtian_jidi": "space-station",
    "chaoxi_jianyu": "tide-prison",
    "az3": "az3",
}


def request_api(api_key):
    """带上 API 密钥请求当天密码；异常信息里不打印完整请求地址。"""
    query = urlencode({"key": api_key, "action": "query", "refresh": "1"})
    request_url = f"{API_URL}?{query}"

    try:
        with urlopen(request_url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"密码 API 返回 HTTP {error.code}") from None
    except URLError as error:
        raise RuntimeError(f"连接密码 API 失败：{error.reason}") from None
    except json.JSONDecodeError:
        raise RuntimeError("密码 API 返回的内容不是有效 JSON") from None


def find_map_list(payload):
    """兼容 maps 在顶层或 data/result 里的响应格式。"""
    current = payload

    for _ in range(3):
        if isinstance(current, dict) and isinstance(current.get("maps"), list):
            return current, current["maps"]

        if isinstance(current, dict):
            nested = current.get("data", current.get("result"))
            if isinstance(nested, dict):
                current = nested
                continue

        break

    raise RuntimeError("响应里没有找到 maps 数组，请检查 API 返回内容")


def convert_response(payload):
    """把 API 的地图对象数组转成网页 script.js 能读取的密码字典。"""
    data, api_maps = find_map_list(payload)
    website_codes = {}

    for api_map in api_maps:
        if not isinstance(api_map, dict):
            continue

        website_id = MAP_ID_TRANSLATION.get(api_map.get("id"))
        password = str(api_map.get("password", ""))

        if website_id and re.fullmatch(r"\d{4}", password):
            website_codes[website_id] = password

    missing_maps = set(MAP_ID_TRANSLATION.values()) - set(website_codes)
    if missing_maps:
        missing_names = ", ".join(sorted(missing_maps))
        raise RuntimeError(f"API 数据缺少地图密码：{missing_names}")

    if data.get("is_today") is False:
        raise RuntimeError("API 返回的不是今日数据，保留现有 codes.json")

    return {
        "updatedAt": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "maps": website_codes,
    }


def main():
    api_key = os.environ.get("DELTA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少 DELTA_API_KEY；请在 GitHub Actions Secrets 中添加 API 密钥")

    new_data = convert_response(request_api(api_key))
    OUTPUT_FILE.write_text(
        json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("codes.json 已更新：6 张地图的密码已写入。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"更新失败：{error}", file=sys.stderr)
        sys.exit(1)
