import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from common import load_conversations


class LoadConversationsTests(unittest.TestCase):
    def write_shards(self, root: Path, shards: dict[str, object]) -> None:
        for name, data in shards.items():
            (root / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def write_zip(self, path: Path, files: dict[str, object]) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, json.dumps(data, ensure_ascii=False))

    def test_extracted_shards_match_zip_for_modern_and_legacy_data(self) -> None:
        cases = (
            [
                {"uuid": "modern-a", "name": "éclair 🌊", "chat_messages": []},
                {"uuid": "modern-b", "name": "Ωmega", "chat_messages": []},
            ],
            [
                {"id": "legacy-a", "title": "old café", "mapping": {}},
                {"id": "legacy-b", "title": "old Ω", "mapping": {}},
            ],
        )

        for conversations in cases:
            with self.subTest(schema="modern" if "chat_messages" in conversations[0] else "legacy"), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir) / "export"
                root.mkdir()
                shards = {
                    "conversations-b.json": [conversations[1]],
                    "conversations-a.json": [conversations[0]],
                }
                self.write_shards(root, shards)
                archive = Path(temp_dir) / "export.zip"
                self.write_zip(archive, shards)

                self.assertEqual(load_conversations(root), load_conversations(archive))
                self.assertEqual(
                    [row.get("id") or row.get("uuid") for row in load_conversations(root)[0]],
                    [conversations[0].get("id") or conversations[0].get("uuid"), conversations[1].get("id") or conversations[1].get("uuid")],
                )
                title_key = "name" if "name" in conversations[0] else "title"
                self.assertEqual(
                    [row[title_key] for row in load_conversations(root)[0]],
                    [conversations[0][title_key], conversations[1][title_key]],
                )

    def test_directory_named_like_shard_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_shards(
                root,
                {
                    "conversations-a.json": [{"id": "kept", "mapping": {}}],
                },
            )
            (root / "conversations-b.json").mkdir()

            conversations, schema = load_conversations(root)

            self.assertEqual([row["id"] for row in conversations], ["kept"])
            self.assertEqual(schema, "legacy")

    def test_monolithic_file_has_priority_over_shards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "conversations.json").write_text(
                json.dumps([{"id": "monolithic", "mapping": {}}]), encoding="utf-8"
            )
            (root / "conversations-a.json").write_text("not json", encoding="utf-8")

            conversations, schema = load_conversations(root)

            self.assertEqual([row["id"] for row in conversations], ["monolithic"])
            self.assertEqual(schema, "legacy")

    def test_invalid_monolithic_file_is_rejected_even_when_shards_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "conversations.json").write_text("null", encoding="utf-8")
            self.write_shards(root, {"conversations-a.json": [{"id": "shard", "mapping": {}}]})

            with self.assertRaisesRegex(SystemExit, r"Expected conversations\.json list"):
                load_conversations(root)

    def test_missing_conversation_data_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(SystemExit, r"Could not find conversation data"):
                load_conversations(Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
