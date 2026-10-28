"""Real file-loading regressions for montage image ownership."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from create_montage import _load_images_with_placeholders


LIMITED_RUNNER = r"""
import resource, runpy, sys
from pathlib import Path
scripts, root, mode = sys.argv[1:]
sys.path.insert(0, scripts)
from create_montage import _load_images_with_placeholders
_, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (32, hard))
if mode == 'cli':
    sys.argv = [str(Path(scripts) / 'create_montage.py'), '--input_dir', root,
                '--output_file', str(Path(root) / 'montage.png'), '--num_col', '8',
                '--cell_width', '8', '--cell_height', '8', '--gap', '2', '--label_mode', 'none']
    runpy.run_path(sys.argv[0], run_name='__main__')
else:
    paths = [str(Path(root) / f'slide-{i}.png') for i in range(48)]
    labels, images = _load_images_with_placeholders(paths, mode == 'retain')
    try:
        assert len(labels) == len(images) == 48
        assert all(image is not None for image in images), 'valid PNGs became placeholders'
        for i, image in enumerate(images):
            assert image.getpixel((0, 0)) == (i * 5 % 256, i * 11 % 256, i * 17 % 256)
    finally:
        for image in images:
            if image is not None:
                image.close()
"""


class MontageLoadingTests(unittest.TestCase):
    def make_images(self, root):
        for i in range(48):
            with Image.new("RGB", (8, 8), (i * 5 % 256, i * 11 % 256, i * 17 % 256)) as image:
                image.save(root / f"slide-{i}.png")

    def run_limited(self, root, mode):
        import resource

        hard = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if hard != resource.RLIM_INFINITY and hard < 32:
            self.skipTest("requires at least 32 file descriptors")
        result = subprocess.run(
            [sys.executable, "-c", LIMITED_RUNNER, str(SCRIPTS), str(root), mode],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])

    @unittest.skipUnless(os.name == "posix", "requires a POSIX file-descriptor limit")
    def test_loads_many_images_without_holding_their_files_open(self):
        for mode in ("temporary", "retain"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_images(root)
                self.run_limited(root, mode)

    @unittest.skipUnless(os.name == "posix", "requires a POSIX file-descriptor limit")
    def test_cli_renders_every_valid_image_under_a_descriptor_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_images(root)
            self.run_limited(root, "cli")
            with Image.open(root / "montage.png") as montage:
                for i in range(48):
                    pixel = (2 + (i % 8) * 10 + 4, 2 + (i // 8) * 10 + 4)
                    self.assertEqual(montage.getpixel(pixel), (i * 5 % 256, i * 11 % 256, i * 17 % 256))

    def test_missing_images_keep_placeholder_and_strict_error_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "valid.png"
            with Image.new("RGB", (8, 8), "green") as image:
                image.save(image_path)
            paths = [str(image_path), str(root / "missing.png")]
            with contextlib.redirect_stdout(io.StringIO()):
                labels, images = _load_images_with_placeholders(paths, False)
            try:
                self.assertEqual(labels, ["valid.png", "missing.png"])
                self.assertEqual(images[0].getpixel((0, 0)), (0, 128, 0))
                self.assertIsNone(images[1])
            finally:
                for image in images:
                    if image is not None:
                        image.close()
            with self.assertRaises(FileNotFoundError):
                _load_images_with_placeholders([paths[1]], False, fail_on_image_error=True)


if __name__ == "__main__":
    unittest.main()
