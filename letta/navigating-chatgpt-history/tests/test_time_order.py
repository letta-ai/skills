import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("history_common", SCRIPTS / "common.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

EARLY = "2026-01-02T01:00:00+02:00"
LATE = "2026-01-01T23:30:00Z"


class TimeOrderTests(unittest.TestCase):
    def test_offsets_sort_by_instant(self):
        self.assertLess(common.sort_key_for_time(EARLY), common.sort_key_for_time(LATE))
        self.assertEqual(
            common.sort_key_for_time(EARLY),
            common.sort_key_for_time("2026-01-01T23:00:00Z"),
        )

    def test_missing_numeric_and_naive_times_remain_sortable(self):
        self.assertLess(common.sort_key_for_time(None), common.sort_key_for_time(0))
        self.assertLess(common.sort_key_for_time(0), common.sort_key_for_time(1))
        self.assertLess(
            common.sort_key_for_time("2026-01-01T23:00:00"), common.sort_key_for_time(LATE)
        )
        self.assertEqual(common.normalize_iso(EARLY), EARLY)

    def test_unrecognized_or_out_of_range_dates_remain_sortable(self):
        for value in ("unknown", "0001-01-01T00:00:00+14:00"):
            with self.subTest(value=value):
                self.assertEqual(common.sort_key_for_time(value), (1, value))

    def test_messages_use_chronological_order(self):
        messages = [
            {"uuid": "late", "created_at": LATE, "text": "Late"},
            {"uuid": "early", "created_at": EARLY, "text": "Early"},
        ]
        rows = common.conversation_messages({"chat_messages": messages}, "modern")
        self.assertEqual([row["text"] for row in rows], ["Early", "Late"])

    def run_script(self, script, *args):
        conversations = [
            {
                "uuid": label.lower(), "name": label,
                "created_at": time, "updated_at": time,
                "chat_messages": [
                    {"uuid": label, "sender": "human", "created_at": time, "text": "needle " + label}
                ],
            }
            for label, time in (("Early", EARLY), ("Late", LATE))
        ]
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "conversations.json").write_text(json.dumps(conversations), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / script), directory, *args],
                capture_output=True, text=True, check=True,
            )
        return result.stdout

    def test_list_recency_in_both_directions(self):
        for field in ("updated", "created"):
            for flags, expected in (([], ["Late", "Early"]), (["--oldest-first"], ["Early", "Late"])):
                with self.subTest(field=field, flags=flags):
                    rows = json.loads(self.run_script("list-conversations.py", "--json", "--sort", field, *flags))
                    self.assertEqual([row["title"] for row in rows], expected)

    def test_search_returns_latest_instant_first(self):
        rows = json.loads(self.run_script("search-conversations.py", "--json", "--query", "needle"))
        self.assertEqual([row["title"] for row in rows], ["Late", "Early"])

    def test_inspection_spans_follow_instants(self):
        output = self.run_script("inspect-export.py")
        span = f"{EARLY} → {common.normalize_iso(LATE)}"
        self.assertIn("Created span: " + span, output)
        self.assertIn("Updated span: " + span, output)
        self.assertLess(output.index("- Late —"), output.index("- Early —"))


if __name__ == "__main__":
    unittest.main()
