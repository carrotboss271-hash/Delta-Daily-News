"""离线验收每日密码更新和 Pages 自动发布判断。"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import should_deploy_pages
import update_codes


WEBSITE_CODES = {
    "zero-dam": "8277",
    "longbow-creek": "6736",
    "buckshot": "2158",
    "space-station": "0826",
    "tide-prison": "0699",
    "az3": "8820",
}
CURRENT_PAYLOAD = {"updatedAt": "2026-11-24T12:42:44+08:00", "maps": WEBSITE_CODES}
API_MAPS = [
    {"id": api_id, "password": WEBSITE_CODES[website_id]}
    for api_id, website_id in update_codes.MAP_ID_TRANSLATION.items()
]


class DailyCodeTests(unittest.TestCase):
    def write_codes(self, path, updated_at):
        path.write_text(
            json.dumps({"updatedAt": updated_at, "maps": WEBSITE_CODES}),
            encoding="utf-8",
        )

    def test_current_beijing_day_with_six_valid_codes_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codes.json"
            self.write_codes(path, "2026-11-24T00:17:00+08:00")

            self.assertTrue(update_codes.has_valid_today_codes(path, date(2026, 11, 24)))

    def test_previous_beijing_day_triggers_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codes.json"
            self.write_codes(path, "2026-11-23T23:59:59+08:00")

            self.assertFalse(update_codes.has_valid_today_codes(path, date(2026, 11, 24)))

    def test_korean_midnight_is_still_previous_beijing_day(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codes.json"
            self.write_codes(path, "2026-11-24T00:30:00+09:00")

            self.assertFalse(update_codes.has_valid_today_codes(path, date(2026, 11, 24)))

    def test_today_with_invalid_map_does_not_skip_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codes.json"
            self.write_codes(path, "2026-11-24T00:17:00+08:00")
            invalid = json.loads(path.read_text(encoding="utf-8"))
            invalid["maps"]["az3"] = "725"
            path.write_text(json.dumps(invalid), encoding="utf-8")

            self.assertFalse(update_codes.has_valid_today_codes(path, date(2026, 11, 24)))

    def test_scheduled_run_skips_api_when_data_is_current(self):
        with patch.object(update_codes, "has_valid_today_codes", return_value=True):
            with patch.object(update_codes, "request_api") as request_api:
                update_codes.main(skip_if_today=True)

        request_api.assert_not_called()

    def test_scheduled_run_fetches_when_data_is_from_yesterday(self):
        with patch.object(update_codes, "has_valid_today_codes", return_value=False):
            with patch.object(update_codes, "update_codes") as update:
                with patch.dict("os.environ", {"DELTA_API_KEY": "test-key"}):
                    update_codes.main(skip_if_today=True)

        update.assert_called_once_with("test-key")

    def test_old_upstream_response_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codes.json"
            original = '{"updatedAt":"2026-11-23T10:00:00+08:00","maps":{}}\n'
            path.write_text(original, encoding="utf-8")
            with patch.object(
                update_codes,
                "request_api",
                return_value={"is_today": False, "maps": API_MAPS},
            ):
                with self.assertRaisesRegex(RuntimeError, "不是今日数据"):
                    update_codes.update_codes("test-key", path)

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_automatic_publish_skips_only_when_live_data_matches(self):
        self.assertFalse(should_deploy_pages.should_deploy(CURRENT_PAYLOAD, CURRENT_PAYLOAD.copy()))
        self.assertTrue(should_deploy_pages.should_deploy(CURRENT_PAYLOAD, {"updatedAt": "yesterday"}))
        self.assertTrue(should_deploy_pages.should_deploy(CURRENT_PAYLOAD, None))

    def test_pages_workflow_has_one_fifteen_second_retry(self):
        workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")

        self.assertEqual(workflow.count("uses: actions/deploy-pages@v5"), 2)
        self.assertEqual(workflow.count("if: steps.deployment.outcome == 'failure'"), 2)
        self.assertIn("run: sleep 15", workflow)


if __name__ == "__main__":
    unittest.main()
