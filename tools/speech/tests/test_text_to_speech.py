"""Offline retry-delay regressions; no SDK client or API key is needed."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "text_to_speech.py"
spec = importlib.util.spec_from_file_location("speech_under_test", SCRIPT)
speech = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speech)


class SpeechRetryTests(unittest.TestCase):
    def test_fractional_message_delays_are_not_truncated(self):
        for message, expected in [
            ("Retry-After: 0.5", 0.5),
            ("retry after 1.75", 1.75),
            ("retry-after=12.25", 12.25),
        ]:
            with self.subTest(message=message):
                self.assertEqual(speech._extract_retry_after_seconds(Exception(message)), expected)

    def test_integer_zero_and_numeric_attributes_keep_their_values(self):
        self.assertEqual(speech._extract_retry_after_seconds(Exception("retry-after=3")), 3.0)
        self.assertEqual(speech._extract_retry_after_seconds(Exception("retry-after: 0")), 0.0)
        for attribute in ("retry_after", "retry_after_seconds"):
            with self.subTest(attribute=attribute):
                error = Exception("retry-after: 99")
                setattr(error, attribute, 0.75)
                self.assertEqual(speech._extract_retry_after_seconds(error), 0.75)

    def test_messages_without_supported_delay_return_none(self):
        for message in ("temporary failure", "retry-after: later", "retry-after: -1"):
            with self.subTest(message=message):
                self.assertIsNone(speech._extract_retry_after_seconds(Exception(message)))

    def test_audio_retry_waits_for_the_fractional_delay(self):
        calls = []

        @contextmanager
        def create(**payload):
            calls.append(payload)
            if len(calls) == 1:
                raise TimeoutError("Retry-After: 0.5")
            yield SimpleNamespace(stream_to_file=lambda path: path.write_bytes(b"test response bytes"))

        client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(
            with_streaming_response=SimpleNamespace(create=create)
        )))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speech.mp3"
            with mock.patch.object(speech, "_ensure_api_key"), mock.patch.object(speech.time, "sleep") as sleep:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    speech._write_audio(client, {"input": "test"}, output, dry_run=False, force=False, attempts=2)
                sleep.assert_called_once_with(0.5)
            self.assertEqual(len(calls), 2)
            self.assertEqual(output.read_bytes(), b"test response bytes")


if __name__ == "__main__":
    unittest.main()
