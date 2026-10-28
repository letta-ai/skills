"""Offline file-write regressions; no SDK, credentials or synthesis required."""

from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "text_to_speech.py"
SPEC = importlib.util.spec_from_file_location("speech", SCRIPT)
speech = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(speech)


def client_for(*writers):
    calls = []
    remaining = iter(writers)

    @contextmanager
    def create(**payload):
        calls.append(payload)
        yield SimpleNamespace(stream_to_file=next(remaining))

    client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(
        with_streaming_response=SimpleNamespace(create=create)
    )))
    return client, calls


def partial_failure(path):
    Path(path).write_bytes(b"partial")
    raise TimeoutError("stream interrupted")


class AtomicOutputTests(unittest.TestCase):
    def write(self, client, output, **kwargs):
        with patch.object(speech, "_ensure_api_key"), patch.object(speech.time, "sleep"):
            speech._write_audio(client, {"input": "fixture"}, output,
                                dry_run=False, force=kwargs.get("force", False),
                                attempts=kwargs.get("attempts", 1))

    def test_failed_force_write_preserves_existing_output_and_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "speech.mp3"
            output.write_bytes(b"original")
            output.chmod(0o640)
            original_mode = stat.S_IMODE(output.stat().st_mode)
            client, _ = client_for(partial_failure)
            with self.assertRaises(TimeoutError):
                self.write(client, output, force=True)
            self.assertEqual(output.read_bytes(), b"original")
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), original_mode)
            self.assertEqual(list(Path(temporary).iterdir()), [output])

    def test_failed_new_output_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "speech.mp3"
            client, _ = client_for(partial_failure)
            with self.assertRaises(TimeoutError):
                self.write(client, output)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_retry_publishes_only_the_completed_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "speech.mp3"
            client, calls = client_for(partial_failure, lambda path: Path(path).write_bytes(b"complete"))
            self.write(client, output, attempts=2)
            self.assertEqual(output.read_bytes(), b"complete")
            self.assertEqual(len(calls), 2)
            self.assertEqual(list(Path(temporary).iterdir()), [output])

    def test_existing_output_without_force_makes_no_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "speech.mp3"
            output.write_bytes(b"original")
            client, calls = client_for()
            with self.assertRaises(SystemExit):
                self.write(client, output)
            self.assertEqual(calls, [])
            self.assertEqual(output.read_bytes(), b"original")

    @unittest.skipIf(os.name == "nt", "symlink creation may require Windows privileges")
    def test_force_write_follows_symlink_and_preserves_target_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.mp3"
            target.write_bytes(b"original")
            target.chmod(0o640)
            mode = stat.S_IMODE(target.stat().st_mode)
            output = root / "speech.mp3"
            output.symlink_to(target.name)
            client, _ = client_for(lambda path: Path(path).write_bytes(b"complete"))
            self.write(client, output, force=True)
            self.assertTrue(output.is_symlink())
            self.assertEqual(target.read_bytes(), b"complete")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), mode)
            self.assertEqual(set(root.iterdir()), {output, target})

    def test_no_force_does_not_overwrite_output_created_during_stream(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "speech.mp3"

            def complete(path):
                Path(path).write_bytes(b"complete")
                output.write_bytes(b"another writer")

            client, _ = client_for(complete)
            with self.assertRaises(FileExistsError):
                self.write(client, output)
            self.assertEqual(output.read_bytes(), b"another writer")
            self.assertEqual(list(Path(temporary).iterdir()), [output])


if __name__ == "__main__":
    unittest.main()
