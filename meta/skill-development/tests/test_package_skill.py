import contextlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from package_skill import package_skill


class PackageSkillTests(unittest.TestCase):
    def test_output_location_does_not_change_packaged_content(self):
        for destination in ("outside", "root", "nested"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as root:
                root = Path(root)
                skill = root / "example-skill"
                skill.mkdir()
                (skill / "SKILL.md").write_text(
                    "---\nname: example-skill\ndescription: Example packaging fixture\n---\n",
                    encoding="utf-8",
                )
                (skill / "assets").mkdir()
                (skill / "assets" / "example.bin").write_bytes(bytes(range(256)))
                output = {
                    "outside": root / "dist",
                    "root": skill,
                    "nested": skill / "dist",
                }[destination]

                # Repack into the same destination as well as creating a fresh archive.
                for _ in range(2):
                    with contextlib.redirect_stdout(io.StringIO()):
                        result = package_skill(skill, output)
                    self.assertIsNotNone(result)
                    with zipfile.ZipFile(result) as archive:
                        self.assertEqual(
                            set(archive.namelist()),
                            {"example-skill/SKILL.md", "example-skill/assets/example.bin"},
                        )
                        self.assertIsNone(archive.testzip())
                        self.assertEqual(
                            archive.read("example-skill/assets/example.bin"), bytes(range(256))
                        )


if __name__ == "__main__":
    unittest.main()
