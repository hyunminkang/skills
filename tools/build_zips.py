#!/usr/bin/env python3
"""Package every skill under skills/ as upload-ready zips in zip/.

  python3 tools/build_zips.py [--skip-tests]

For each skills/<name>/SKILL.md it writes:
  zip/claude/<name>.zip   <name>/SKILL.md inside the zip: Claude.ai, Claude
                          Code, ChatGPT, Codex and most skill loaders
  zip/gemini/<name>.zip   SKILL.md at the zip root, as Gemini requires for
                          multi-file skills
Both zips carry the repository's LICENSE as LICENSE.txt.

Gemini accepts only certain file types in a skill (plain text it recognizes
by extension, PDFs and images). In the Gemini zip, a text file with any other
extension gets ".txt" appended (e.g. checks.R -> checks.R.txt); an
unsupported binary file stops the build.

Before packaging it checks each SKILL.md frontmatter (name matches the
folder, lowercase-hyphen name of at most 64 characters, description of 1-200
characters: Claude.ai's limit, stricter than the open spec's 1024), checks that no skill folder holds a .zip (Claude.ai rejects a
skill zip that contains another zip; built packages belong in samples/), and
runs the test suite in tests/, so a broken skill is never zipped. Entries are sorted and time-stamped 1980-01-01, so an unchanged skill
produces byte-identical zips.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
ZIPS = ROOT / "zip"
LICENSE = ROOT / "LICENSE"
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "extracted"}
SKIP_FILES = {".DS_Store", ".Rhistory", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".bak"}
# File types Gemini accepts in a skill (support.google.com/gemini/answer/17094296)
GEMINI_EXTENSIONS = {".txt", ".md", ".rst", ".rtf", ".tex", ".log", ".py", ".sh",
                     ".json", ".yaml", ".csv", ".toml", ".xml", ".env", ".sql",
                     ".html", ".css", ".svg", ".pdf", ".jpg", ".jpeg", ".png",
                     ".gif", ".webp"}
GEMINI_NAMES = {"Makefile", "Dockerfile"}


def gemini_name(name: str, path: Path) -> str:
    """The name a file gets in the Gemini zip; raises for unsupported binaries."""
    if Path(name).suffix.lower() in GEMINI_EXTENSIONS or Path(name).name in GEMINI_NAMES:
        return name
    try:
        path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"{path} is binary and Gemini does not accept its type")
    return name + ".txt"


def members(skill: Path) -> list[Path]:
    out = []
    for p in sorted(skill.rglob("*")):
        rel = p.relative_to(skill)
        if p.is_dir() or any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in SKIP_FILES or p.suffix in SKIP_SUFFIXES:
            continue
        out.append(p)
    return out


def load_yaml(text: str):
    """Parse YAML with PyYAML, or with the pure-Python copy bundled in a skill."""
    try:
        import yaml
    except ImportError:
        vendored = sorted(SKILLS.glob("*/scripts/_vendor"))
        if not vendored:
            raise
        sys.path.insert(0, str(vendored[0]))
        import yaml
    return yaml.safe_load(text)


def check_frontmatter(skill: Path) -> list[str]:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return [f"{skill.name}: SKILL.md has no YAML frontmatter"]
    try:   # hosts parse the frontmatter as YAML; e.g. an unquoted ': ' breaks it
        front = load_yaml(m.group(1))
    except Exception as exc:
        return [f"{skill.name}: SKILL.md frontmatter is not valid YAML ({exc})"]
    if not isinstance(front, dict):
        return [f"{skill.name}: SKILL.md frontmatter must be a mapping"]
    front = {k: str(v) for k, v in front.items()}
    problems = []
    unknown = set(front) - {"name", "description", "license", "allowed-tools",
                            "metadata", "dependencies"}
    if unknown:
        problems.append(f"{skill.name}: unknown frontmatter field(s) {sorted(unknown)}; "
                        f"some hosts reject them")
    if front.get("name") != skill.name:
        problems.append(f"{skill.name}: frontmatter name {front.get('name')!r} "
                        f"!= folder name")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", front.get("name", "")):
        problems.append(f"{skill.name}: name must be lowercase letters, digits and "
                        f"hyphens, at most 64 characters")
    desc = front.get("description", "")
    if not desc or len(desc) > 200:   # Claude.ai's upload limit; the spec allows 1024
        problems.append(f"{skill.name}: description must be 1-200 characters "
                        f"(has {len(desc)}); Claude.ai rejects longer ones")
    for z in members(skill):
        try:
            gemini_name(z.name, z)
        except ValueError as exc:
            problems.append(f"{skill.name}: {exc}")
        if z.suffix.lower() == ".zip":
            problems.append(f"{skill.name}: {z.relative_to(skill)} is a zip inside the "
                            f"skill; Claude.ai rejects nested zips. Move it to samples/ "
                            f"or delete it.")
    return problems


def write_zip(path: Path, prefix: str, skill: Path, gemini: bool = False) -> list[str]:
    def add(zf, name: str, data: bytes, mode: int):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = mode << 16
        zf.writestr(info, data)

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        entries = [(prefix + p.relative_to(skill).as_posix(), p) for p in members(skill)]
        if LICENSE.is_file() and not (skill / "LICENSE.txt").exists():
            entries.append((prefix + "LICENSE.txt", LICENSE))
        renamed = []
        if gemini:
            mapped = [(gemini_name(n, p), p) for n, p in entries]
            renamed = [f"{n} -> {m}" for (n, _), (m, _) in zip(entries, mapped) if n != m]
            entries = mapped
        for name, p in sorted(entries):
            add(zf, name, p.read_bytes(), 0o755 if p.suffix == ".py" else 0o644)
    return renamed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-tests", action="store_true", help="do not run tests/ first")
    a = ap.parse_args()

    skills = sorted(p.parent for p in SKILLS.glob("*/SKILL.md"))
    if not skills:
        print("no skills/<name>/SKILL.md found", file=sys.stderr)
        return 1
    problems = [p for s in skills for p in check_frontmatter(s)]
    for p in problems:
        print(f"ERROR {p}", file=sys.stderr)
    if problems:
        return 1
    if not a.skip_tests and (ROOT / "tests").is_dir():
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                            "-q"], cwd=ROOT)
        if r.returncode != 0:
            print("tests failed; no zips written", file=sys.stderr)
            return 1
    for skill in skills:
        for zip_path, prefix, gemini in (
                (ZIPS / "claude" / f"{skill.name}.zip", f"{skill.name}/", False),
                (ZIPS / "gemini" / f"{skill.name}.zip", "", True)):
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            renamed = write_zip(zip_path, prefix, skill, gemini)
            print(f"Wrote {zip_path.relative_to(ROOT)}: "
                  f"{zip_path.stat().st_size / 1024:.0f} KB"
                  + (f"; renamed for Gemini: {', '.join(renamed)}" if renamed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
