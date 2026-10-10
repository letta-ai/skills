"""Regression tests for the minimal skill frontmatter validator."""

import tempfile
import unittest
from pathlib import Path

from quick_validate import validate_skill


class ValidateSkillTests(unittest.TestCase):
    def validate_frontmatter(self, frontmatter):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'SKILL.md').write_text(
                f'---\n{frontmatter}\n---\n\n# Example skill\n'
            )
            return validate_skill(directory)

    def test_valid_frontmatter(self):
        self.assertEqual(
            self.validate_frontmatter('name: example-skill\ndescription: Example skill.'),
            (True, 'Skill is valid!'),
        )

    def test_indented_root_fields(self):
        for indentation in ('  ', '    '):
            with self.subTest(indentation=indentation):
                self.assertEqual(
                    self.validate_frontmatter(
                        '# An unindented comment does not change mapping indentation.\n'
                        f'{indentation}name: example-skill\n'
                        f'{indentation}description: Example skill.'
                    ),
                    (True, 'Skill is valid!'),
                )

    def test_indented_fields_with_multiline_quoted_description(self):
        for description in ('"first\nsecond"', '"first\n  second\n"'):
            with self.subTest(description=description):
                self.assertEqual(
                    self.validate_frontmatter(
                        f'  name: example-skill\n  description: {description}'
                    ),
                    (True, 'Skill is valid!'),
                )

    def test_indented_nested_fields_keep_existing_behavior(self):
        self.assertEqual(
            self.validate_frontmatter(
                '  metadata:\n    name: example-skill\n  description: Example skill.'
            ),
            (True, 'Skill is valid!'),
        )

    def test_root_anchor_and_tag_keep_existing_behavior(self):
        for prefix in ('&skill', '!!map'):
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    self.validate_frontmatter(
                        f'{prefix}\n  name: example-skill\n  description: Example skill.'
                    ),
                    (True, 'Skill is valid!'),
                )

    def test_comments_do_not_supply_required_fields(self):
        for field, other in (
            ('name', 'description: Example skill.'),
            ('description', 'name: example-skill'),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.validate_frontmatter(f'# {field}: example\n{other}'),
                    (False, f"Missing '{field}' in frontmatter"),
                )

    def test_other_keys_do_not_supply_required_fields(self):
        for field, other in (
            ('name', 'description: Example skill.'),
            ('description', 'name: example-skill'),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.validate_frontmatter(f'other-{field}: example\n{other}'),
                    (False, f"Missing '{field}' in frontmatter"),
                )

    def test_nested_fields_keep_existing_behavior(self):
        for field, other in (
            ('name', 'description: Example skill.'),
            ('description', 'name: example-skill'),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.validate_frontmatter(f'metadata:\n  {field}: example\n{other}'),
                    (True, 'Skill is valid!'),
                )

    def test_comments_do_not_override_valid_fields(self):
        self.assertEqual(
            self.validate_frontmatter(
                '# name: Invalid Name\n# description: <example>\n'
                'name: example-skill\ndescription: Example skill.'
            ),
            (True, 'Skill is valid!'),
        )

    def test_comments_do_not_hide_invalid_fields(self):
        cases = (
            ('# name: example-skill\nname: Invalid Name\ndescription: Example skill.',
             "Name 'Invalid Name' should be hyphen-case (lowercase letters, digits, and hyphens only)"),
            ('# description: Example skill.\nname: example-skill\ndescription: <example>',
             'Description cannot contain angle brackets (< or >)'),
        )
        for frontmatter, message in cases:
            with self.subTest(frontmatter=frontmatter):
                self.assertEqual(self.validate_frontmatter(frontmatter), (False, message))


if __name__ == '__main__':
    unittest.main()
