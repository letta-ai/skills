"""Run with python -m unittest discover -s letta/letta-filesystem-to-memfs/scripts."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("letta_fs_to_memfs.py")
spec = importlib.util.spec_from_file_location("letta_fs_to_memfs", SCRIPT)
memfs = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = memfs
spec.loader.exec_module(memfs)


class ChunkTextTests(unittest.TestCase):
    def assert_bounded_and_complete(self, source, size, overlap):
        normalized = memfs.normalize_text(source)
        chunks = memfs.chunk_text(source, size, overlap)
        self.assertTrue(chunks)
        covered = 0
        previous = None
        for index, chunk in enumerate(chunks, 1):
            self.assertEqual(chunk.index, index)
            self.assertLessEqual(len(chunk.text), size)
            self.assertLessEqual(chunk.char_end - chunk.char_start, size)
            self.assertLessEqual(chunk.char_start, covered)
            self.assertGreater(chunk.char_end, covered)
            self.assertEqual(chunk.text.strip(), normalized[chunk.char_start:chunk.char_end].strip())
            if previous is not None:
                self.assertEqual(chunk.char_start, previous.char_end - overlap)
            covered = chunk.char_end
            previous = chunk
        self.assertFalse(normalized[covered:].strip())
        return chunks

    def test_default_size_long_paragraph(self):
        self.assert_bounded_and_complete("abcdefghij" * 1000, 3000, 300)

    def test_short_intro_does_not_swallow_long_paragraph(self):
        self.assert_bounded_and_complete("Introduction\n\n" + "content " * 150, 80, 10)

    def test_small_sizes_and_large_overlap_make_progress(self):
        for size, overlap in [(1, 0), (2, 1), (80, 0), (80, 79)]:
            with self.subTest(size=size, overlap=overlap):
                self.assert_bounded_and_complete("café日本語" * 30, size, overlap)

    def test_paragraph_boundaries_are_preferred(self):
        first = "a" * 240 + "\n \n"
        source = first + "b" * 240
        chunks = self.assert_bounded_and_complete(source, 300, 30)
        self.assertEqual(chunks[0].char_end, len(first))

    def test_empty_input_and_invalid_limits(self):
        self.assertEqual(memfs.chunk_text(" \r\n\t\n", 80, 10), [])
        for size, overlap in [(0, 0), (-1, 0), (80, -1), (80, 80)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    memfs.chunk_text("text", size, overlap)

    def test_ingest_cli_exports_bounded_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.md"
            source.write_text("Introduction\r\n\r\n" + "café日本語 " * 150, encoding="utf-8")
            output = root / "memory"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "ingest", "--source", str(source),
                 "--memory-dir", str(output), "--corpus", "sample", "--chunk-size", "80",
                 "--overlap", "10", "--no-system-index", "--json"],
                check=True, capture_output=True, text=True,
            )
            summary = json.loads(result.stdout)
            rows = [json.loads(line) for line in (output / "documents/sample/chunks.jsonl").read_text().splitlines()]
            self.assertEqual(summary["chunks"], len(rows))
            self.assertGreater(len(rows), 1)
            for row in rows:
                self.assertLessEqual(len(row["content"]), 80)
                self.assertLessEqual(row["metadata"]["char_end"] - row["metadata"]["char_start"], 80)
                self.assertTrue((output / row["path"]).is_file())
            self.assertFalse((output / "system").exists())


if __name__ == "__main__":
    unittest.main()
