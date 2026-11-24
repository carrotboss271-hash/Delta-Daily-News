"""从每日密码 API 获取数据，并整理成网页使用的 codes.json。"""

import json
import os
import re
import sys
from datetime import date, datetime
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
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
EXPECTED_MAP_IDS = frozenset(MAP_ID_TRANSLATION.values())


def has_valid_today_codes(output_file=OUTPUT_FILE, today=None):
    """检查现有文件是否包含北京时间当天的六张有效地图密码。"""
    try:
        current = json.loads(Path(output_file).read_text(encoding="utf-8"))
        updated_at = datetime.fromisoformat(current["updatedAt"])
        maps = current["maps"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False

    if not isinstance(maps, dict) or set(maps) != EXPECTED_MAP_IDS:
        return False
    if any(not isinstance(password, str) or not re.fullmatch(r"\d{4}", password) for password in maps.values()):
        return False

    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=BEIJING_TZ)
    data_date = updated_at.astimezone(BEIJING_TZ).date()
    if today is None:
        today = datetime.now(BEIJING_TZ).date()
    return data_date == today


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
        "updatedAt": datetime.now(BEIJING_TZ).isoformat(timespec="seconds"),
        "maps": website_codes,
    }


def update_codes(api_key, output_file=OUTPUT_FILE):
    """校验 API 响应后再原子替换文件，避免旧数据或写入中断损坏现有文件。"""
    new_data = convert_response(request_api(api_key))
    output_file = Path(output_file)
    temporary_file = output_file.with_name(f".{output_file.name}.tmp")
    try:
        temporary_file.write_text(
            json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_file.replace(output_file)
    finally:
        temporary_file.unlink(missing_ok=True)


def main(skip_if_today=False):
    if skip_if_today and has_valid_today_codes():
        print("codes.json 已有北京时间当天的六张有效密码，跳过 API 请求和提交。")
        return

    api_key = os.environ.get("DELTA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少 DELTA_API_KEY；请在 GitHub Actions Secrets 中添加 API 密钥")

    update_codes(api_key)
    print("codes.json 已更新：6 张地图的密码已写入。")


if __name__ == "__main__":
    try:
        main(skip_if_today="--skip-if-today" in sys.argv[1:])
    except Exception as error:
        print(f"更新失败：{error}", file=sys.stderr)
        sys.exit(1)
