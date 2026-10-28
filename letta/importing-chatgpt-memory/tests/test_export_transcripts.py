"""Run with: python -m unittest discover -s letta/importing-chatgpt-memory/tests."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export-transcripts.py"
SPEC = importlib.util.spec_from_file_location("export_transcripts", SCRIPT)
export_transcripts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export_transcripts)


def frontmatter(text):
    marker, header, body = text.split("---\n", 2)
    assert marker == ""
    return yaml.safe_load(header), body


class ExportFrontmatterTests(unittest.TestCase):
    def test_descriptions_round_trip_as_yaml_strings(self):
        for description in (
            "Transcript export for ChatGPT conversation 0: Planning",
            'Quotes "and" \\ paths # tags: café 😀',
            "First line\n---\nSecond line\r\nwith\ttabs",
            "true",
        ):
            with self.subTest(description=description):
                result = export_transcripts.add_frontmatter(
                    "# Transcript\n", description=description, limit=500
                )
                metadata, body = frontmatter(result)
                self.assertEqual(metadata, {"description": description, "limit": 500})
                self.assertEqual(body, "# Transcript\n")

    def test_cli_exports_parseable_single_and_chunked_frontmatter(self):
        title = 'Planning: "café" # notes'
        conversation = {"id": "example", "title": title, "mapping": {}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "export.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("conversations-000.json", json.dumps([conversation]))
            for max_chars in (40000, 100):
                with self.subTest(max_chars=max_chars):
                    output = root / str(max_chars)
                    subprocess.run(
                        [sys.executable, str(SCRIPT), str(archive), "--output-dir", str(output),
                         "--indexes", "0", "--memory-frontmatter", "--max-chars", str(max_chars)],
                        check=True, capture_output=True, text=True,
                    )
                    transcripts = sorted(output.glob("chatgpt-*.md"))
                    self.assertGreater(len(transcripts), 0)
                    if max_chars == 100:
                        self.assertGreater(len(transcripts), 1)
                    for part, transcript in enumerate(transcripts, start=1):
                        metadata, body = frontmatter(transcript.read_text(encoding="utf-8"))
                        suffix = f" part {part}/{len(transcripts)}" if len(transcripts) > 1 else ""
                        self.assertEqual(metadata, {
                            "description": f"Transcript export for ChatGPT conversation 0{suffix}: {title}",
                            "limit": 500,
                        })
                        self.assertTrue(body)
                    metadata, body = frontmatter((output / "index.md").read_text(encoding="utf-8"))
                    self.assertEqual(metadata, {
                        "description": "Index of exported ChatGPT transcript files", "limit": 500
                    })
                    self.assertIn("# ChatGPT transcript export", body)

    def test_cli_without_frontmatter_preserves_plain_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "export.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("conversations-000.json", json.dumps([{"title": "Notes", "mapping": {}}]))
            output = root / "output"
            subprocess.run(
                [sys.executable, str(SCRIPT), str(archive), "--output-dir", str(output), "--indexes", "0"],
                check=True, capture_output=True, text=True,
            )
            self.assertTrue(next(output.glob("chatgpt-*.md")).read_text().startswith("# Notes\n"))
            self.assertTrue((output / "index.md").read_text().startswith("# ChatGPT transcript export\n"))


if __name__ == "__main__":
    unittest.main()
