"""自动发布前比较 Pages 与仓库中的 codes.json。"""

import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODES_URL = "https://carrotboss271-hash.github.io/Delta-Daily-News/codes.json"
EXPECTED_MAP_IDS = {
    "zero-dam",
    "longbow-creek",
    "buckshot",
    "space-station",
    "tide-prison",
    "az3",
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_live_codes(url):
    """读取线上文件并绕过缓存；读取失败由调用方按需要发布处理。"""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["_check"] = str(int(time.time()))
    request_url = urlunsplit(parts._replace(query=urlencode(query)))
    request = Request(request_url, headers={"Cache-Control": "no-cache"})

    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def should_deploy(repository_codes, live_codes):
    """线上内容未知或与仓库不同则发布。"""
    if not is_valid_codes_payload(repository_codes) or not is_valid_codes_payload(live_codes):
        return True
    return repository_codes != live_codes


def is_valid_codes_payload(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("maps"), dict):
        return False
    if set(payload["maps"]) != EXPECTED_MAP_IDS:
        return False
    if any(not isinstance(password, str) or not re.fullmatch(r"\d{4}", password) for password in payload["maps"].values()):
        return False
    try:
        datetime.fromisoformat(payload["updatedAt"])
    except (KeyError, TypeError, ValueError):
        return False
    return True


def main():
    output_file = os.environ.get("GITHUB_OUTPUT")
    url = os.environ.get("PAGES_CODES_URL", DEFAULT_CODES_URL)
    deploy = True

    try:
        repository_codes = read_json(REPOSITORY_ROOT / "codes.json")
        live_codes = fetch_live_codes(url)
        deploy = should_deploy(repository_codes, live_codes)
        if deploy:
            print("Pages 的 codes.json 与仓库不同；继续发布。")
        else:
            print("Pages 的 codes.json 与仓库一致；跳过上传。")
    except (OSError, ValueError, URLError, TimeoutError) as error:
        print(f"无法可靠读取 Pages 或仓库 codes.json（{error}）；继续发布。", file=sys.stderr)

    result = f"deploy={'true' if deploy else 'false'}\n"
    if output_file:
        with open(output_file, "a", encoding="utf-8") as output:
            output.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
