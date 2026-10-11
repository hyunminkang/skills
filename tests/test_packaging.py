"""Packaging rules every host enforces on uploaded skill zips."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_zips  # noqa: E402

SKILLS = sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))


class PackagingTest(unittest.TestCase):
    def test_frontmatter(self):
        for skill in SKILLS:
            self.assertEqual(build_zips.check_frontmatter(skill), [], skill.name)

    def test_gemini_accepts_every_file(self):
        for skill in SKILLS:
            for p in build_zips.members(skill):
                name = build_zips.gemini_name(p.name, p)
                self.assertTrue(Path(name).suffix.lower() in build_zips.GEMINI_EXTENSIONS
                                or name in build_zips.GEMINI_NAMES, name)

    def test_no_nested_zip(self):
        for skill in SKILLS:
            self.assertFalse([p for p in build_zips.members(skill)
                              if p.suffix.lower() == ".zip"], skill.name)


if __name__ == "__main__":
    unittest.main()
